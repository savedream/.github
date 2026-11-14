"""조직 README용 GIF 3개: 대화 데모(demo.gif), 한 턴의 흐름(pipeline.gif), 메트로놈(metronome.gif)."""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
MONO = "/System/Library/Fonts/Menlo.ttc"
WEIGHT = {"r": 0, "m": 2, "sb": 4, "b": 6, "xb": 14}

BG = (11, 18, 32)
PANEL = (22, 32, 51)
PANEL2 = (30, 43, 66)
BORDER = (51, 65, 85)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
RED = (239, 68, 68)
ORANGE = (249, 115, 22)
YELLOW = (234, 179, 8)
GREEN = (34, 197, 94)
TEAL = (20, 184, 166)
BLUE = (59, 130, 246)
VIOLET = (139, 92, 246)
WHITE = (255, 255, 255)


@lru_cache
def font(size: int, weight: str = "r") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size, index=WEIGHT[weight])


@lru_cache
def mono(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(MONO, size)


def text_w(d: ImageDraw.ImageDraw, s: str, f) -> int:
    return int(d.textlength(s, font=f))


def wrap(d: ImageDraw.ImageDraw, s: str, f, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in s.split(" "):
        cand = word if not cur else cur + " " + word
        if text_w(d, cand, f) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:  # 한 단어가 줄보다 길면 글자 단위로
            if text_w(d, cur + ch, f) > max_w and cur:
                lines.append(cur)
                cur = ""
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def mix(a, b, t: float):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def pill(d, x, y, label, color, f, pad=10, h=28, fill=None, dot=True):
    w = text_w(d, label, f) + pad * 2 + (14 if dot else 0)
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill or PANEL2, outline=mix(color, BG, 0.4))
    tx = x + pad
    if dot:
        d.ellipse((x + pad, y + h // 2 - 4, x + pad + 8, y + h // 2 + 4), fill=color)
        tx += 14
    d.text((tx, y + h // 2), label, font=f, fill=TEXT, anchor="lm")
    return w


def draw_heart(d, cx, cy, size, color):
    pts = []
    for i in range(60):
        t = math.pi * 2 * i / 60
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * size / 17, cy - y * size / 17))
    d.polygon(pts, fill=color)


def save_gif(frames: list[Image.Image], durations: list[int], path: Path) -> None:
    """여러 장면에서 색을 모아 팔레트 하나를 만들고 모든 장면에 같은 팔레트를 쓴다(깜빡임과 용량을 줄임)."""
    sample = frames[:: max(1, len(frames) // 10)] + [frames[-1]]
    w, h = frames[0].size
    strip = Image.new("RGB", (w, h * len(sample)))
    for i, f in enumerate(sample):
        strip.paste(f, (0, h * i))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    out = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out[0].save(path, save_all=True, append_images=out[1:], duration=durations, loop=0, optimize=True,
                disposal=1)


# ---------------------------------------------------------------- 1. 대화 데모
W, H = 960, 540
CHAT = (24, 78, 596, 520)
SIDE = (616, 78, 936, 520)
ROLE_COLOR = {"question": ORANGE, "instruction": BLUE, "notice": TEAL}
ROLE_LABEL = {"question": "질문", "instruction": "안내", "notice": "알림"}
STATUS = {"speaking": ("안내 중", BLUE), "armed": ("듣고 있어요", GREEN), "capturing": ("말하는 중", ORANGE),
          "processing": ("처리 중", YELLOW)}


@lru_cache(maxsize=256)
def _bubble(who: str, text: str, role: str | None, screen: str | None, width: int) -> Image.Image:
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    max_w = 400
    if who == "user":
        f = font(17, "m")
        lines = wrap(d, text, f, max_w - 32) or [""]
        bw = max(text_w(d, ln, f) for ln in lines) + 32
        bh = 20 + 26 * len(lines)
        img = Image.new("RGBA", (width, bh), (0, 0, 0, 0))
        g = ImageDraw.Draw(img)
        x0 = width - bw - 4
        g.rounded_rectangle((x0, 0, width - 4, bh), radius=16, fill=(234, 88, 12))
        for i, ln in enumerate(lines):
            g.text((x0 + 16, 12 + 26 * i), ln, font=f, fill=WHITE)
        return img
    f, fh, fc = font(16), font(13, "b"), font(11, "b")
    lines = wrap(d, text, f, max_w - 36)
    color = ROLE_COLOR.get(role, TEAL)
    chip = ROLE_LABEL.get(role, "알림")
    cw = text_w(d, chip, fc) + 14
    bw = max([text_w(d, ln, f) for ln in lines] + [cw + 8 + text_w(d, screen or "", fh)]) + 36
    bh = 18 + 24 * len(lines) + (24 if screen else 0)
    img = Image.new("RGBA", (width, bh), (0, 0, 0, 0))
    g = ImageDraw.Draw(img)
    g.rounded_rectangle((4, 0, 4 + bw, bh), radius=16, fill=PANEL2)
    g.rounded_rectangle((4, 0, 10, bh), radius=3, fill=color)
    y = 10
    if screen:
        g.rounded_rectangle((22, y, 22 + cw, y + 18), radius=9, fill=mix(color, PANEL2, 0.55))
        g.text((22 + cw // 2, y + 9), chip, font=fc, fill=WHITE, anchor="mm")
        g.text((22 + cw + 8, y + 9), screen, font=fh, fill=mix(color, WHITE, 0.35), anchor="lm")
        y += 24
    for i, ln in enumerate(lines):
        g.text((22, y + 24 * i), ln, font=f, fill=TEXT)
    return img


def bubble_img(b: dict, width: int) -> Image.Image:
    return _bubble(b["who"], b["text"], b.get("role"), b.get("screen"), width)


def demo_frame(st: dict, ms: int) -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    phase = ms / 1000
    # 위쪽 막대: 로고, 듣기 상태, GPS
    d.rectangle((0, 0, W, 60), fill=PANEL)
    d.ellipse((22, 14, 54, 46), fill=RED)
    d.rectangle((35, 20, 41, 40), fill=WHITE)
    d.rectangle((28, 27, 48, 33), fill=WHITE)
    d.text((66, 30), "살려드림", font=font(24, "xb"), fill=WHITE, anchor="lm")
    d.text((172, 32), "통신이 안 되는 곳의 응급 안내 키트", font=font(13), fill=MUTED, anchor="lm")
    label, color = STATUS[st["status"]]
    x = W - 24
    gps = "GPS 37.402180, 127.679420"
    gw = text_w(d, gps, font(13, "m")) + 34
    pill(d, x - gw, 16, gps, GREEN, font(13, "m"), fill=mix(PANEL2, GREEN, 0.4 * st["gps_flash"]))
    x -= gw + 12
    sw = text_w(d, label, font(14, "b")) + 74
    d.rounded_rectangle((x - sw, 16, x, 44), radius=14, fill=PANEL2, outline=mix(color, BG, 0.3))
    pulse = 0.5 + 0.5 * math.sin(phase * 6)
    d.ellipse((x - sw + 12, 26, x - sw + 20, 34), fill=mix(color, WHITE, 0.4 * pulse))
    d.text((x - sw + 28, 30), label, font=font(14, "b"), fill=TEXT, anchor="lm")
    bx = x - 34
    for i in range(4):  # 말소리·안내 중이면 막대가 움직이고, 처리 중이면 차례로 켜짐
        live = st["status"] in ("capturing", "speaking")
        amp = (0.35 + 0.65 * abs(math.sin(phase * 9 + i * 1.3))) if live else 0.25
        if st["status"] == "processing":
            amp = 0.9 if int(phase * 8) % 4 == i else 0.25
        hgt = int(16 * amp)
        d.rounded_rectangle((bx + i * 6, 30 - hgt // 2, bx + i * 6 + 3, 30 + hgt // 2), radius=1, fill=color)
    # 대화창: 말풍선을 위에서부터 쌓고 아래쪽이 보이게 자른다(스크롤)
    cx0, cy0, cx1, cy1 = CHAT
    cw, ch = cx1 - cx0, cy1 - cy0
    d.rounded_rectangle((cx0 - 8, cy0 - 6, cx1 + 8, cy1 + 8), radius=18, fill=PANEL)
    imgs = [bubble_img(b, cw) for b in st["bubbles"]]
    total = sum(i.height + 8 for i in imgs)
    tall = Image.new("RGBA", (cw, max(total + 30, ch)), (0, 0, 0, 0))
    y = 6
    for k, bi in enumerate(imgs):
        if k == len(imgs) - 1 and st["enter"] < 1:  # 새 말풍선이 살짝 올라오며 나타남
            t = st["enter"]
            fade = bi.copy()
            fade.putalpha(bi.getchannel("A").point(lambda a, t=t: int(a * t)))
            tall.alpha_composite(fade, (0, y + int(14 * (1 - t))))
        else:
            tall.alpha_composite(bi, (0, y))
        y += bi.height + 8
    top = max(0, y + 4 - ch)
    layer = tall.crop((0, top, cw, top + ch))
    if top > 0:  # 위로 밀려난 말풍선은 위쪽 가장자리에서 서서히 사라지게
        alpha = layer.getchannel("A")
        fade = Image.linear_gradient("L").resize((cw, 256)).crop((0, 0, cw, 40)).resize((cw, 40))
        alpha.paste(ImageChops.multiply(alpha.crop((0, 0, cw, 40)), fade), (0, 0))
        layer.putalpha(alpha)
    im.paste(layer, (cx0, cy0), layer)
    # 오른쪽: 지금 진행할 단계
    sx0, sy0, sx1, sy1 = SIDE
    d.rounded_rectangle((sx0, sy0 - 6, sx1, sy0 + 196), radius=18, fill=PANEL)
    d.text((sx0 + 20, sy0 + 18), "지금 진행하세요", font=font(13, "b"), fill=MUTED, anchor="lm")
    card = st["card"]
    started = card["manual"] != "상황 확인 중"
    mw = pill(d, sx0 + 20, sy0 + 36, card["manual"], RED if started else MUTED, font(13, "b"),
              fill=mix(PANEL2, RED, 0.25) if started else PANEL2)
    if card.get("kind"):
        kc = ORANGE if card["kind"] == "질문" else BLUE
        pill(d, sx0 + 28 + mw, sy0 + 36, card["kind"], kc, font(13, "b"), dot=False, fill=mix(PANEL2, kc, 0.3))
    ty = sy0 + 80
    for ln in wrap(d, card["title"], font(22, "xb"), sx1 - sx0 - 40)[:3]:
        d.text((sx0 + 20, ty), ln, font=font(22, "xb"), fill=WHITE)
        ty += 30
    d.text((sx0 + 20, sy0 + 176), card.get("step", ""), font=mono(12), fill=MUTED, anchor="lm")
    # 오른쪽 아래: 기기
    dy = sy0 + 210
    d.rounded_rectangle((sx0, dy, sx1, sy1 + 8), radius=18, fill=PANEL)
    d.text((sx0 + 20, dy + 22), "기기", font=font(13, "b"), fill=MUTED, anchor="lm")
    rows = [("메트로놈", st["metro"], RED), ("구조신호", "꺼짐", MUTED), ("타이머", st["timer"], GREEN),
            ("교대 알림", st["alert"], YELLOW)]
    for i, (name, val, vc) in enumerate(rows):
        ry = dy + 40 + i * 48
        d.rounded_rectangle((sx0 + 14, ry, sx1 - 14, ry + 44), radius=12, fill=PANEL2)
        d.text((sx0 + 30, ry + 22), name, font=font(15, "b"), fill=TEXT, anchor="lm")
        on = val not in ("꺼짐", "대기", "00:00")
        if name == "메트로놈" and on:
            beat = (ms % 545) / 545  # 분당 110회
            draw_heart(d, sx1 - 140, ry + 23, 9 + 5 * max(0.0, 1 - beat * 4), RED)
        d.text((sx1 - 30, ry + 22), val, font=font(15, "xb") if on else font(15), fill=vc if on else MUTED,
               anchor="rm")
    return im


def build_demo(transcript: dict, out: Path) -> None:
    frames, durs = [], []
    st = {"status": "speaking", "bubbles": [], "enter": 1, "gps_flash": 0, "metro": "꺼짐", "timer": "00:00",
          "alert": "대기", "card": {"manual": "상황 확인 중", "title": "어떤 상황인지 말씀해 주세요"}}
    clock = {"ms": 0, "timer_from": None, "alert_end": None}
    speed = 7  # 데모라 시계는 7배속

    def emit(dur: int):
        if clock["timer_from"] is not None:
            sec = (clock["ms"] - clock["timer_from"]) * speed // 1000
            st["timer"] = f"{sec // 60:02d}:{sec % 60:02d}"
        if clock["alert_end"] is not None:
            left = max(0, (clock["alert_end"] - clock["ms"]) * speed // 1000)
            st["alert"] = f"{left // 60}:{left % 60:02d} 남음"
        frames.append(demo_frame(st, clock["ms"]))
        durs.append(dur)
        clock["ms"] += dur

    def hold(ms: int, step: int = 180):
        for _ in range(max(1, ms // step)):
            emit(step)

    def kit_says(e: dict, after: int):
        st["status"] = "speaking"
        st["bubbles"].append(e)
        for t in (0.3, 0.6, 0.85):
            st["enter"] = t
            emit(60)
        st["enter"] = 1
        hold(after)

    def user_says(text: str):
        st["status"] = "armed"
        hold(540)
        st["status"] = "capturing"
        st["bubbles"].append({"who": "user", "text": ""})
        for i in range(1, len(text) + 1):
            st["bubbles"][-1] = {"who": "user", "text": text[:i]}
            emit(70)
        hold(300, 100)
        st["status"] = "processing"
        hold(720, 90)

    for e in transcript["log"]:
        if e["who"] == "user":
            user_says(e["text"])
            continue
        sid, tid = e.get("step_id"), e.get("template_id")
        if e.get("source") == "intro":
            st["card"] = {"manual": "EM-01 심정지 의심", "title": "심정지가 의심됩니다", "step": "intro_tts"}
        elif sid:
            st["card"] = {"manual": "EM-01 심정지 의심", "title": e["screen"], "step": sid,
                          "kind": "질문" if e["role"] == "question" else "안내"}
        if tid == "T_GPS_OK":
            st["gps_flash"] = 1
        if sid == "EM01-07":  # metronome:on:110, timer:start
            st["metro"] = "110 BPM"
            clock["timer_from"] = clock["ms"]
        if sid == "EM01-09":  # alert:120 (2분 뒤 교대)
            clock["alert_end"] = clock["ms"] + 120000 // speed
        kit_says(e, after=min(2600, 700 + 38 * len(e["text"])))
        st["gps_flash"] = 0
    st["status"] = "armed"
    st["card"] = {"manual": "EM-01 심정지 의심", "title": "계속 누르세요 (2분 뒤 교대)", "step": "EM01-15", "kind": "안내"}
    hold(3200)
    save_gif(frames, durs, out)


# ---------------------------------------------------------------- 2. 한 턴의 흐름
PW, PH = 960, 330
STAGES = [
    ("음성 입력", "silero VAD", RED),
    ("STT", "SenseVoice", ORANGE),
    ("정규화", "학습 문장 형식으로", YELLOW),
    ("모델", "Llama-3.2-1B + LoRA", GREEN),
    ("출력 파서", "함수 호출 검사", TEAL),
    ("절차 엔진", "매뉴얼 DB v1.7", BLUE),
    ("TTS, 기기", "VITS, 메트로놈, GPS", VIOLET),
]
DATA = [
    ("", "wave"),
    ("\"사람이 쓰러졌는데 숨을 안 쉬어\"", "ko"),
    ("문장부호 제거, 숫자는 한글로  →  사람이 쓰러졌는데 숨을 안 쉬어", "ko"),
    ("<maum_0>(situation=1, conscious=-1, breathing=0, ...)<maum_end>", "mono"),
    ("report_situation    situation=1 (심정지)    breathing=0 (없음)", "ko"),
    ("EM-01 심정지 의심  →  EM01-01 반응 확인    안내 문장은 매뉴얼 원문만", "ko"),
    ("\"심정지가 의심됩니다. 어깨를 두드리며 크게 불렀을 때 대답을 하나요?\"", "ko"),
]


def pipe_frame(active: int, travel: float, ms: int) -> Image.Image:
    im = Image.new("RGB", (PW, PH), BG)
    d = ImageDraw.Draw(im)
    d.text((24, 30), "한 턴의 흐름", font=font(22, "xb"), fill=WHITE, anchor="lm")
    d.text((160, 32), "인터넷 없이 키트 안에서 모두 처리", font=font(14), fill=MUTED, anchor="lm")
    tag = "목표: 말이 끝나고 3초 안에 첫 안내"
    tw = text_w(d, tag, font(13, "b")) + 24
    d.rounded_rectangle((PW - 24 - tw, 17, PW - 24, 43), radius=13, fill=mix(PANEL2, GREEN, 0.25))
    d.text((PW - 24 - tw // 2, 30), tag, font=font(13, "b"), fill=TEXT, anchor="mm")
    bw, gap, x0, y0, bh = 118, 16, 24, 70, 104
    for i, (title, sub, color) in enumerate(STAGES):
        x = x0 + i * (bw + gap)
        on = i == active and travel >= 1
        done = i < active or on
        fill = mix(PANEL, color, 0.3) if on else (mix(PANEL, color, 0.1) if done else PANEL)
        d.rounded_rectangle((x, y0, x + bw, y0 + bh), radius=16, fill=fill,
                            outline=color if on else mix(color, BG, 0.55), width=3 if on else 2)
        d.ellipse((x + 12, y0 + 12, x + 38, y0 + 38), fill=color)
        d.text((x + 25, y0 + 25), str(i + 1), font=font(15, "xb"), fill=WHITE, anchor="mm")
        d.text((x + 12, y0 + 58), title, font=font(16, "xb"), fill=WHITE, anchor="lm")
        for k, ln in enumerate(wrap(d, sub, font(11, "m"), bw - 20)[:2]):
            d.text((x + 12, y0 + 78 + k * 14), ln, font=font(11, "m"), fill=MUTED, anchor="lm")
        if i < len(STAGES) - 1:
            ax, ay = x + bw + 2, y0 + bh // 2
            d.line((ax, ay, ax + gap - 6, ay), fill=BORDER, width=3)
            d.polygon([(ax + gap - 7, ay - 5), (ax + gap - 1, ay), (ax + gap - 7, ay + 5)], fill=BORDER)
    if active > 0 and travel < 1:  # 다음 단계로 넘어가는 점
        px = x0 + (active - 1) * (bw + gap) + bw + gap * travel
        c = STAGES[active][2]
        d.ellipse((px - 9, y0 + bh // 2 - 9, px + 9, y0 + bh // 2 + 9), fill=mix(c, WHITE, 0.3))
    c = STAGES[active][2]
    d.rounded_rectangle((24, 200, PW - 24, 300), radius=16, fill=PANEL, outline=mix(c, BG, 0.4), width=2)
    d.rounded_rectangle((24, 200, 32, 300), radius=4, fill=c)
    d.text((48, 224), f"{active + 1}. {STAGES[active][0]}", font=font(14, "b"), fill=mix(c, WHITE, 0.35), anchor="lm")
    if travel < 1:
        return im
    text, kind = DATA[active]
    if kind == "wave":
        d.text((PW - 44, 224), "말소리 구간을 잘라 냄 (16 kHz, 32ms 단위)", font=font(12), fill=MUTED, anchor="rm")
        for k in range(72):
            amp = abs(math.sin(k * 0.5 + ms / 90)) * (0.4 + 0.6 * abs(math.sin(k * 0.13)))
            h = int(20 * amp) + 2
            d.rounded_rectangle((48 + k * 12, 264 - h, 48 + k * 12 + 6, 264 + h), radius=3, fill=c)
    else:
        f = mono(15) if kind == "mono" else font(18, "b")
        d.text((48, 264), text, font=f, fill=TEXT, anchor="lm")
    return im


def build_pipeline(out: Path) -> None:
    frames, durs, ms = [], [], 0

    def add(a, t, dur):
        nonlocal ms
        frames.append(pipe_frame(a, t, ms))
        durs.append(dur)
        ms += dur

    for a in range(len(STAGES)):
        if a > 0:
            for t in (0.2, 0.45, 0.7, 0.95):
                add(a, t, 60)
        for _ in range(10):
            add(a, 1, 100)
    for _ in range(14):
        add(len(STAGES) - 1, 1, 100)
    save_gif(frames, durs, out)


# ---------------------------------------------------------------- 3. 메트로놈
def build_metronome(out: Path) -> None:
    mw, mh = 360, 200
    frames, durs = [], []
    for k, amp in enumerate((1.0, 0.75, 0.5, 0.25, 0.0, 0.0)):
        im = Image.new("RGB", (mw, mh), BG)
        d = ImageDraw.Draw(im)
        cx, cy = 92, 100
        for r, a in ((70, 0.14), (56, 0.22)):
            rr = r + int(18 * (1 - amp))
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=mix(BG, RED, a * (0.4 + amp)), width=3)
        draw_heart(d, cx, cy + 4, 34 + 10 * amp, mix(RED, (255, 130, 130), amp * 0.5))
        d.text((180, 78), "110", font=font(44, "xb"), fill=WHITE, anchor="lm")
        d.text((262, 86), "BPM", font=font(18, "b"), fill=RED, anchor="lm")
        d.text((182, 124), "가슴압박 박자를 부저로", font=font(14, "m"), fill=MUTED, anchor="lm")
        frames.append(im)
        durs.append(90 if k < 5 else 545 - 90 * 5)  # 한 박 545ms = 분당 110회
    save_gif(frames, durs, out)


if __name__ == "__main__":
    transcript_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    build_demo(json.loads(transcript_path.read_text(encoding="utf-8")), out_dir / "demo.gif")
    build_pipeline(out_dir / "pipeline.gif")
    build_metronome(out_dir / "metronome.gif")
    for p in sorted(out_dir.glob("*.gif")):
        with Image.open(p) as g:
            print(p.name, g.size, g.n_frames, "frames", f"{p.stat().st_size / 1024:.0f} KB")
