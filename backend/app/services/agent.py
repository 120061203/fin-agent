import asyncio
import json
import os
from datetime import datetime
from typing import AsyncGenerator

import litellm

from app.models.comparison import ComparisonJob, ComparisonStatus, ReasoningStep, StepType
from app.services import indexer
from app.services.session_manager import session_manager


def _llm_call(messages: list, max_tokens: int = 4096) -> str:
    base_url = os.getenv("LITELLM_BASE_URL", "https://lllm.xsong.us")
    api_key = os.getenv("LITELLM_API_KEY", "")
    model = os.getenv("LITELLM_MODEL", "claude-sonnet-4-6")

    response = litellm.completion(
        model=model,
        messages=messages,
        api_base=base_url,
        api_key=api_key,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def run_comparison(job: ComparisonJob) -> AsyncGenerator[ReasoningStep, None]:
    step_n = [0]

    def make_step(stype: StepType, content: str) -> ReasoningStep:
        step_n[0] += 1
        step = ReasoningStep(
            step_id=step_n[0],
            job_id=job.job_id,
            type=stype,
            content=content,
            timestamp=datetime.utcnow(),
        )
        job.steps.append(step)
        return step

    try:
        job.status = ComparisonStatus.running
        pdf_a = session_manager.get_pdf(job.pdf_id_a)
        pdf_b = session_manager.get_pdf(job.pdf_id_b)

        yield make_step(StepType.info, f"正在讀取文件 A：{pdf_a.filename}（{pdf_a.chunk_count} 個段落）")
        await asyncio.sleep(0)
        yield make_step(StepType.info, f"正在讀取文件 B：{pdf_b.filename}（{pdf_b.chunk_count} 個段落）")
        await asyncio.sleep(0)
        yield make_step(StepType.thinking, "正在分析兩份文件的主要主題...")
        await asyncio.sleep(0)

        # Step 1: Topic Discovery
        intro_a = " ".join(indexer.search(job.pdf_id_a, "摘要 目的 概述 introduction", top_k=5))[:3000]
        intro_b = " ".join(indexer.search(job.pdf_id_b, "摘要 目的 概述 introduction", top_k=5))[:3000]

        topic_prompt = (
            f"你是一位財務文件分析專家。以下是兩份文件的節選內容。\n"
            f"請列出 3~6 個值得比較的主要主題，以 JSON 陣列回傳，例如：[\"服務範圍\", \"財務狀況\", \"風險因素\"]\n\n"
            f"文件 A 節選：\n{intro_a}\n\n文件 B 節選：\n{intro_b}\n\n"
            f"請只回傳 JSON 陣列，不要其他說明。"
        )

        topics_raw = await asyncio.get_event_loop().run_in_executor(
            None, _llm_call, [{"role": "user", "content": topic_prompt}]
        )

        try:
            # Extract JSON array from response
            import re
            match = re.search(r'\[.*\]', topics_raw, re.DOTALL)
            topics = json.loads(match.group()) if match else ["財務表現", "業務概況", "風險因素"]
            if not isinstance(topics, list) or len(topics) == 0:
                topics = ["財務表現", "業務概況", "風險因素"]
        except Exception:
            topics = ["財務表現", "業務概況", "風險因素"]

        yield make_step(
            StepType.thinking,
            "已識別以下比較主題：\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics)),
        )
        await asyncio.sleep(0)

        # Step 2: Per-topic comparison
        topic_results = []
        for i, topic in enumerate(topics):
            yield make_step(StepType.thinking, f"正在比較主題：{topic}（第 {i+1}/{len(topics)} 個）")
            await asyncio.sleep(0)

            chunks_a = indexer.search(job.pdf_id_a, topic, top_k=3)
            chunks_b = indexer.search(job.pdf_id_b, topic, top_k=3)
            context_a = "\n---\n".join(chunks_a)[:4000]
            context_b = "\n---\n".join(chunks_b)[:4000]

            compare_prompt = (
                f"你是財務文件比較專家。請比較以下兩份文件中關於「{topic}」的內容。\n\n"
                f"文件 A（{pdf_a.filename}）：\n{context_a}\n\n"
                f"文件 B（{pdf_b.filename}）：\n{context_b}\n\n"
                f"請以繁體中文輸出以下格式的 JSON：\n"
                f'{{\"topic\": \"{topic}\", \"similarities\": [\"...\"], \"differences\": [\"...\"], \"risks\": [\"...\"]}}'
            )

            result_raw = await asyncio.get_event_loop().run_in_executor(
                None, _llm_call, [{"role": "user", "content": compare_prompt}]
            )

            try:
                import re
                match = re.search(r'\{.*\}', result_raw, re.DOTALL)
                result = json.loads(match.group()) if match else {}
                if "topic" not in result:
                    result["topic"] = topic
            except Exception:
                result = {"topic": topic, "similarities": [], "differences": [result_raw[:300]], "risks": []}

            topic_results.append(result)
            sim_c = len(result.get("similarities", []))
            diff_c = len(result.get("differences", []))
            risk_c = len(result.get("risks", []))
            yield make_step(
                StepType.result,
                f"【{topic}】比較完成：{sim_c} 項相同點、{diff_c} 項差異點、{risk_c} 項風險提示",
            )
            await asyncio.sleep(0)

        # Step 3: Aggregation
        yield make_step(StepType.thinking, "正在彙整所有主題的比較結果，生成最終報告...")
        await asyncio.sleep(0)

        summary_prompt = (
            f"你是財務報告撰寫專家。請根據以下各主題的比較結果，用繁體中文生成一份結構化的差異報告（Markdown 格式）。\n\n"
            f"比較文件：\n- 文件 A：{pdf_a.filename}\n- 文件 B：{pdf_b.filename}\n\n"
            f"各主題比較結果：\n{json.dumps(topic_results, ensure_ascii=False, indent=2)}\n\n"
            f"請生成包含以下結構的 Markdown 報告：\n"
            f"1. 執行摘要（2-3 句話概述主要差異）\n"
            f"2. 各主題詳細比較（每個主題包含：相同點、差異點、風險提示）\n"
            f"3. 整體風險評估"
        )

        report_markdown = await asyncio.get_event_loop().run_in_executor(
            None, _llm_call, [{"role": "user", "content": summary_prompt}], 8192
        )

        job.report_markdown = report_markdown
        job.status = ComparisonStatus.done
        job.completed_at = datetime.utcnow()
        yield make_step(StepType.result, "分析完成！報告已生成。")

    except Exception as e:
        job.status = ComparisonStatus.error
        job.error_message = str(e)
        yield make_step(StepType.result, f"分析過程發生錯誤：{str(e)}")
