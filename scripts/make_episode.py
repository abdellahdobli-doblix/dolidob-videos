"""Writes podcast/script.json for one episode: two states, one salary, figures from dolidob.com's open data.

Usage: python scripts/make_episode.py "Texas" "California" 75000 [data.json]
The dialogue follows the same 11 lines and 8 scenes as the first episode, so the animated scene clips in
podcast/scenes are reused. The cheaper state is always told first. No figure is typed by hand: every number
comes from take-home-2026.json (single filer, paid every two weeks, no 401(k)).
"""
import json
import sys
import urllib.request

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n):
    """Spoken form of a whole number below one million."""
    n = int(n)
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return ONES[n // 100] + " hundred" + (" " + words(n % 100) if n % 100 else "")
    return words(n // 1000) + " thousand" + (" " + words(n % 1000) if n % 1000 else "")


def said(x):
    """Rounded the way a person says it: tens below $10,000, hundreds above."""
    step = 10 if x < 10000 else 100
    return words(round(x / step) * step) + " dollars"


def usd(x):
    return f"${int(x + 0.5):,}"  # half up, like the site (Python's round() would give 61,592 for 61,592.5)


def main():
    a_name, b_name, salary = sys.argv[1], sys.argv[2], int(sys.argv[3])
    src = sys.argv[4] if len(sys.argv) > 4 else "https://dolidob.com/data/take-home-2026.json"
    data = json.load(open(src) if not src.startswith("http") else urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": "dolidob-videos/1.0"})))
    by_name = {s["name"].lower(): s for s in data["states"]}

    def row(name):
        st = by_name[name.lower()]
        r = next(x for x in st["salaries"] if x["salary"] == salary)
        return st, r

    sa, ra = row(a_name)
    sb, rb = row(b_name)
    if ra["takeHome"] < rb["takeHome"]:  # tell the cheaper state first
        sa, ra, sb, rb = sb, rb, sa, ra
    A, B = sa["name"], sb["name"]
    fed = ra["federalIncomeTax"]
    fica = ra["socialSecurity"] + ra["medicare"]
    assert abs(fed - rb["federalIncomeTax"]) < 1 and abs(fica - rb["socialSecurity"] - rb["medicare"]) < 1

    def state_part(st, r):
        tax = r["stateIncomeTax"] + r["stateInsurance"]
        if not st["wageIncomeTax"] and r["stateInsurance"] == 0:
            return f"{st['name']} has no income tax on wages", 0
        extra = f", with {st['insuranceLabel']}" if r["stateInsurance"] > 0 and st.get("insuranceLabel") else ""
        if not st["wageIncomeTax"]:
            return f"{st['name']} has no income tax on wages, but takes about {said(r['stateInsurance'])}{extra}", tax
        return f"{st['name']} takes about {said(tax)}{extra}", tax

    pa, ta = state_part(sa, ra)
    pb, tb = state_part(sb, rb)
    label_b = f"{B} tax" + (" + " + ("SDI" if "SDI" in (sb.get("insuranceLabel") or "") else "insurance") if rb["stateInsurance"] > 0 else "")
    state_card = {"label": label_b, "value": f"-{usd(tb)}", "color": "pink"} if ta == 0 else {"label": f"State tax: {A} vs {B}", "value": f"{usd(ta)} vs {usd(tb)}", "color": "pink"}
    diff = ra["takeHome"] - rb["takeHome"]

    lines = [
        ("dob", f"Doli, I got two job offers. Same pay, {words(salary // 1000)} thousand dollars. One in {A}, one in {B}.", {"label": "Salary", "value": usd(salary), "color": "sky"}, 1),
        ("doli", "Nice! Same salary, but you won't take home the same amount.", None, 2),
        ("dob", "Wait, really? Why not?", None, 2),
        ("doli", f"Federal tax is the same in both: about {said(fed)}.", {"label": "Federal income tax", "value": f"-{usd(fed)}", "color": "sky"}, 3),
        ("doli", f"Social Security and Medicare are the same too: about {said(fica)}.", {"label": "Social Security + Medicare", "value": f"-{usd(fica)}", "color": "violet"}, 4),
        ("dob", "So what's different?", None, 5),
        ("doli", f"The state. {pa}. {pb}.", state_card, 5),
        ("dob", "So how much do I keep?", None, 6),
        ("doli", f"{A}: about {said(ra['takeHome'])}. {B}: about {said(rb['takeHome'])}.", {"label": f"Take-home: {A} vs {B}", "value": f"{usd(ra['takeHome'])} vs {usd(rb['takeHome'])}", "color": "gold"}, 6),
        ("dob", f"That's {said(diff)} a year, just for the state!", None, 7),
        ("doli", "Check your own state and salary free at dolidob dot com. Estimates only, not tax advice.", {"label": "Try it free", "value": "dolidob.com", "color": "gold"}, 8),
    ]
    script = json.load(open("podcast/script.json"))
    script["title"] = f"{A} vs {B} on {usd(salary)} (2026)"
    script["source"] = f"Figures from {src} (single filer, paid every two weeks, no 401(k))."
    script["lines"] = [{"speaker": s, "text": t, **({"card": c} if c else {}), "scene": n} for s, t, c, n in lines]
    json.dump(script, open("podcast/script.json", "w"), indent=2, ensure_ascii=False)
    open("podcast/script.json", "a").write("\n")
    print(script["title"])
    for l in script["lines"]:
        print(f"  {l['speaker']}: {l['text']}" + (f"   [{l['card']['label']}: {l['card']['value']}]" if "card" in l else ""))


main()
