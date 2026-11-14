"""실제 엔진(가짜 부품)으로 심정지 시나리오를 돌려 안내 순서를 JSON으로 뽑는다. 프로젝트 폴더에서 실행한다."""
import asyncio
import json
import sys

from tests.scenario.kit import Kit

TURNS = ["사람이 쓰러졌는데 숨을 안 쉬어", "아니요 대답 없어요", "아니요"]


async def main(out: str) -> None:
    async with Kit() as kit:
        log = [{"who": "kit", **u.model_dump()} for u in kit.spoken]
        for text in TURNS:
            mark = len(kit.spoken)
            await kit.say(text)
            log.append({"who": "user", "text": text})
            log += [{"who": "kit", **u.model_dump()} for u in kit.spoken_since(mark)]
        s = kit.state
        end = {"step_id": s.step_id, "metronome": s.devices["metronome"].status, "timer": s.timer.status,
               "flags": s.flags}
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"log": log, "end": end}, f, ensure_ascii=False, indent=1)


asyncio.run(main(sys.argv[1]))
