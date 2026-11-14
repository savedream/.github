# .github-private

살려드림 조직 멤버에게만 보이는 조직 프로필 저장소입니다. 조직 페이지에는 `profile/README.md`가 표시됩니다.

| 경로 | 내용 |
|---|---|
| `profile/README.md` | 조직 프로필 (소개, 다이어그램, 기능, 팀) |
| `profile/assets/` | 프로필 GIF (대화 데모, 한 턴의 흐름, 메트로놈) |
| `scripts/` | GIF를 다시 만드는 스크립트 |

## GIF 다시 만들기

대화 데모는 Back 저장소의 실제 절차 엔진을 가짜 부품으로 돌려 나온 안내 순서로 그립니다. 매뉴얼 DB가 바뀌면 다시 만들면 됩니다(macOS 글꼴 Apple SD Gothic Neo, Menlo 사용).

```bash
# 1. Back 저장소 폴더에서 심정지 시나리오의 안내 순서를 뽑는다
cd ../Back
PYTHONPATH=. .venv/bin/python ../.github-private/scripts/transcript.py /tmp/transcript.json

# 2. 이 저장소에서 GIF를 그린다 (Pillow 필요)
cd ../.github-private
python -m pip install pillow
python scripts/make_gifs.py /tmp/transcript.json profile/assets
```
