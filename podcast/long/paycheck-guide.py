"""Writes podcast/long/paycheck-guide.json: the 10-minute "Where does my paycheck go?" episode.

Every figure comes from dolidob.com data (2026 rules unless said otherwise):
  - take-home-pay-by-state-2026.csv (single, paid every two weeks, no 401(k))
  - federal brackets and standard deduction: IRS Rev. Proc. 2025-32 (2026) and 2026-35 (2027)
  - Social Security 6.2% to $184,500, Medicare 1.45%, Additional Medicare 0.9%: IRS Pub 15 (2026)
  - bonus withholding 22% / 37% over $1 million: IRS Pub 15 (2026)
  - 401(k) limits: IRS Notice 2025-67 (2026) and 2026-66 (2027); 2027 wage base: SSA COLA fact sheet
Scenes 1-8 are the existing Grok clips in podcast/scenes (see storyboard.md), reused by mood.
"""
import json
import os

D, L = "dob", "doli"
lines = []


def say(speaker, text, scene, card=None):
    item = {"speaker": speaker, "text": text, "scene": scene}
    if card:
        item["card"] = {"label": card[0], "value": card[1], "color": card[2]}
    lines.append(item)


# Chapter 1: the gap between salary and paycheck
say(D, "Doli, I just got my first real job offer. Seventy-five thousand dollars a year!", 1, ("Salary", "$75,000", "sky"))
say(L, "Congratulations! Now the question nobody asks: how much of that actually lands in your bank account?", 2)
say(D, "Seventy-five thousand divided by twenty-six paychecks. About twenty-eight hundred each time, right?", 1)
say(L, "That's your gross pay, before anything comes out. Today let's follow one paycheck from top to bottom and see where every dollar goes.", 3, ("Gross every two weeks", "$2,884.62", "sky"))
say(D, "Okay. Walk me through it. Slowly.", 2)

# Chapter 2: federal income tax
say(L, "First stop: federal income tax. And here's the part most people get wrong. You are not taxed on all seventy-five thousand.", 3)
say(D, "I'm not?", 5)
say(L, "No. In twenty twenty-six, a single filer gets a standard deduction of sixteen thousand one hundred dollars. That part is never taxed.", 3, ("2026 standard deduction", "$16,100", "mint"))
say(L, "So your taxable income is fifty-eight thousand nine hundred.", 4, ("Taxable income", "$58,900", "sky"))
say(D, "And then they take twenty-two percent of that? That's my bracket, isn't it?", 1)
say(L, "Twenty-two percent is your top bracket, but only the last few dollars are taxed at that rate. The tax system works in layers.", 3)
say(L, "The first twelve thousand four hundred is taxed at ten percent. The next part, up to fifty thousand four hundred, at twelve percent. Only the rest is taxed at twenty-two.", 4, ("2026 brackets", "10% · 12% · 22%", "violet"))
say(D, "So what's the total?", 2)
say(L, "Seven thousand six hundred seventy dollars for the year. That's about ten percent of your salary, not twenty-two.", 3, ("Federal income tax", "$7,670", "pink"))
say(D, "Wait, so getting a raise can't make me take home less money?", 7)
say(L, "Never. Only the dollars above the line pay the higher rate. A raise always leaves you with more.", 3)

# Chapter 3: Social Security and Medicare
say(D, "Okay, what's next on the list?", 1)
say(L, "FICA. That's Social Security and Medicare, and they work very differently from income tax.", 3)
say(L, "Social Security is a flat six point two percent of your pay. Medicare is one point four five percent. No deductions, no brackets.", 4, ("Social Security + Medicare", "7.65%", "violet"))
say(D, "So on seventy-five thousand that's...", 2)
say(L, "Four thousand six hundred fifty for Social Security, and one thousand eighty-seven fifty for Medicare.", 4, ("FICA on $75,000", "$5,737.50", "pink"))
say(D, "Does it ever stop?", 1)
say(L, "Social Security does. In twenty twenty-six it stops once your wages pass one hundred eighty-four thousand five hundred. Medicare never stops, and above two hundred thousand an extra zero point nine percent is withheld.", 3, ("2026 wage base", "$184,500", "mint"))

# Chapter 4: the state
say(D, "Federal, Social Security, Medicare. Is that everything?", 2)
say(L, "Not yet. Now comes the part that depends on where you live: state income tax.", 6)
say(D, "Right, my offer has two locations. Texas or California.", 1)
say(L, "Texas takes no income tax from wages. So on seventy-five thousand, you keep about sixty-one thousand five hundred ninety-three dollars a year.", 6, ("Take-home in Texas", "$61,593", "gold"))
say(L, "California takes state income tax, plus one point three percent for state disability insurance. You'd keep about fifty-seven thousand five hundred sixty-five.", 6, ("Take-home in California", "$57,565", "gold"))
say(D, "That's about four thousand dollars a year apart. For the exact same salary!", 5, ("Difference per year", "$4,028", "pink"))
say(L, "And Texas is not alone. Nine states take no income tax from wages: Alaska, Florida, Nevada, New Hampshire, South Dakota, Tennessee, Texas, Washington and Wyoming.", 4, ("States with no wage tax", "9", "mint"))
say(D, "So I should just move to one of those?", 1)
say(L, "Careful. Washington still takes paid family leave and a long-term care program, about a thousand forty dollars on seventy-five thousand. And sales tax, property tax and rent are not in your paycheck at all.", 3)
say(D, "Got it. The paycheck is only one piece of the cost of living.", 2)

# Chapter 4b: filing status and the W-4
say(D, "One more thing. I'm getting married next year. Does that change my paycheck?", 1)
say(L, "It can. Married couples who file jointly get a bigger standard deduction, thirty-two thousand two hundred in twenty twenty-six, and wider brackets.", 3, ("2026 joint standard deduction", "$32,200", "mint"))
say(L, "If you're the only earner on seventy-five thousand, federal income tax drops from seven thousand six hundred seventy to four thousand six hundred forty.", 4, ("Joint federal tax on $75,000", "$4,640", "pink"))
say(L, "In Texas that means your take-home goes up to about sixty-four thousand six hundred twenty-three a year.", 6, ("Married take-home in Texas", "$64,623", "gold"))
say(D, "That's three thousand more a year just for getting married?", 5)
say(L, "When one spouse earns and the other doesn't, yes. When you both work, the extra income fills the brackets faster, so the gap is smaller.", 3)
say(D, "How does my employer even know I'm married?", 2)
say(L, "From your Form W-4. It's the form you fill out when you start a job. It tells payroll your filing status, any second job, your dependents and extra deductions.", 3)
say(L, "If your W-4 is wrong, too much or too little comes out of every paycheck. You only find out when you file your return.", 4)
say(D, "So the W-4 is like the settings menu for my paycheck.", 7)
say(L, "That's a great way to put it. Update it when your life changes: marriage, a baby, a second job.", 3)
say(D, "Got it. Life changes, update the settings.", 1)

# Chapter 5: hourly pay
say(D, "My friend Sam gets paid by the hour. Twenty-five dollars. How does that compare?", 1)
say(L, "Full time is forty hours a week for fifty-two weeks. That's two thousand eighty hours, so twenty-five dollars an hour is fifty-two thousand a year.", 3, ("$25 an hour, full time", "$52,000", "sky"))
say(L, "In a state with no income tax, Sam keeps about forty-three thousand nine hundred sixty-two. That's around three thousand six hundred sixty-four a month.", 6, ("Sam's take-home", "$43,962", "gold"))
say(D, "And when Sam works overtime?", 2)
say(L, "Under federal law, hours over forty in a week are paid at one and a half times the rate. For Sam, that's thirty-seven fifty an hour.", 4, ("Time and a half", "$37.50", "sky"))
say(D, "But his overtime paychecks always look heavily taxed.", 7)
say(L, "That's a withholding trick, not a special tax. Payroll treats a big paycheck as if you earned that much every single week, so it withholds more. Part of it comes back at tax time.", 3)

# Chapter 6: bonuses
say(D, "Okay, what about bonuses? My offer mentions a five-thousand-dollar signing bonus.", 1, ("Signing bonus", "$5,000", "sky"))
say(L, "Employers can withhold a flat twenty-two percent for federal tax on a bonus. That's one thousand one hundred dollars.", 3)
say(L, "Then Social Security and Medicare take another three hundred eighty-two fifty. So you'd see about three thousand five hundred seventeen.", 4, ("Bonus you keep", "$3,517.50", "gold"))
say(D, "Ouch. Is the bonus taxed more than my salary?", 5)
say(L, "No. Twenty-two percent is only the amount held back up front. Your bonus is taxed like any other income when you file, so you may get some back. Only bonuses above one million dollars in a year are withheld at thirty-seven percent.", 3)
say(D, "I'll worry about the million later.", 7)

# Chapter 7: the 401(k)
say(L, "Now the part that can actually lower your taxes: your 401(k).", 6)
say(D, "The retirement thing? I was going to skip it for now.", 2)
say(L, "Here's why you shouldn't. Traditional 401(k) money comes out before federal income tax. Put in six percent, and many employers add a match.", 3)
say(L, "On a sixty-thousand-dollar salary, six percent is three thousand six hundred. A common match of fifty cents per dollar adds another eighteen hundred, free.", 4, ("You + employer match", "$5,400", "gold"))
say(D, "Free money. Okay, I'm listening. Is there a limit?", 1)
say(L, "In twenty twenty-six you can put in up to twenty-four thousand five hundred. At fifty or older, eight thousand more. And from sixty to sixty-three, a higher catch-up of eleven thousand two hundred fifty.", 3, ("2026 401(k) limit", "$24,500", "mint"))
say(D, "Roth or traditional? Everyone argues about that.", 2)
say(L, "Simple rule. If you expect a lower tax rate in retirement, traditional usually wins. If you expect a higher one, Roth wins. Same rate, it's a tie.", 4)

# Chapter 8: 2027
say(D, "And next year? Does all this change?", 1)
say(L, "The numbers move with inflation. In twenty twenty-seven the standard deduction rises to sixteen thousand six hundred, and the brackets get wider.", 3, ("2027 standard deduction", "$16,600", "mint"))
say(L, "On the same seventy-five thousand, federal income tax drops to about seven thousand three hundred eighty-nine. The 401(k) limit rises to twenty-five thousand five hundred.", 4, ("2027 federal tax on $75,000", "$7,389.50", "pink"))
say(L, "And Social Security will apply to wages up to one hundred ninety-two thousand three hundred.", 6, ("2027 wage base", "$192,300", "mint"))

# Chapter 9: recap
say(D, "Let me see if I've got it. Gross pay, minus the standard deduction, then tax in layers.", 2)
say(D, "Plus seven point six five percent for Social Security and Medicare. Plus the state, which can be zero or several thousand.", 1)
say(L, "Exactly. And then your choices: overtime, bonuses, your 401(k), your filing status. Each one changes the number.", 3)
say(D, "So the real question isn't what's my salary. It's what will I actually take home.", 7)
say(L, "That's the one. And you don't have to do the math by hand.", 6)
say(L, "At dolidob dot com there's a free paycheck calculator for every state, plus guides for everything we covered today, all built on official 2026 figures.", 6, ("Free calculators", "dolidob.com", "gold"))
say(D, "Okay, I'm checking both of my offers tonight.", 1)
say(L, "Good plan. These are estimates, not tax advice, so check your real pay stub too. Thanks for listening!", 8)
say(D, "See you next time!", 8)

script = {
    "title": "Where Does My Paycheck Go? The Full 2026 Guide",
    "voices": {"doli": "cgSgspJ2msm6clMCkdW9", "dob": "bIHbv24MWmeRgasZH58o"},
    "kokoroVoices": {"doli": "af_heart", "dob": "am_michael"},
    "geminiVoices": {"doli": "Aoede", "dob": "Puck"},
    "geminiStyle": {
        "dob": "Say in a casual, curious young man's voice, natural podcast pace",
        "doli": "Say in a warm, confident young woman's voice, clear and friendly, natural podcast pace",
    },
    "source": "Figures from dolidob.com open data and IRS/SSA publications (2026 rules; 2027 where stated).",
    "end": {"dob": "celebrate", "doli": "point"},
    "lines": lines,
}
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "paycheck-guide.json"), "w") as f:
    json.dump(script, f, indent=1, ensure_ascii=False)
words = sum(len(l["text"].split()) for l in lines)
print(f"{len(lines)} lines, {words} words, about {words / 150:.1f} minutes at 150 words a minute")
