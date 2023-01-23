import openai

from flask import Flask, make_response, redirect, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
	limitation = request.cookies.get("limit_user") or "no"
	response = make_response(render_template("index.html", limit_user = limitation))
	response.set_cookie("limit_user", "no")
	return response

@app.route("/cards", methods = ["GET", "POST"])
def cards():
	openai.api_key = request.form["api_key"]

	try:
	    models = openai.Model.list()
	    print(models)
	except (openai.error.AuthenticationError, openai.error.RateLimitError):
	    response = redirect("/", 302)
	    response.set_cookie("limit_user", "yes")
	    return response

	topic = request.form["topic"]
	num_cards = int(request.form["num_cards"])
	all_cards = []

	if is_medical(topic):
		all_cards = generate_cards(topic, num_cards)
	else:
		num_cards = 0
		all_cards = [""]

		if topic.strip() == "":
			topic = "[no topic]"

	response = make_response(render_template("cards.html", topic = topic, num_cards = num_cards, all_cards = all_cards))
	response.set_cookie("limit_user", "no")

	return response

def is_medical(topic):
	example_1 = "Is [infection] related to medicine? yes\n"
	example_2 = "Is [laparoscopic appendectomy] related to medicine? yes\n"
	example_3 = "Is [the study of knitting] related to medicine? no\n"
	example_4 = "Is [hiv] related to medicine? yes\n"
	example_5 = "Is [statin] related to medicine? yes\n"
	example_6 = "Is [beauty] related to medicine? no\n"
	example_7 = "Is [the news] related to medicine? no\n"
	example_8 = "Is [foster] related to medicine? no\n"

	examples = example_1 + example_2 + example_3 + example_4 + example_5 + example_6 + example_7 + example_8

	prompt = examples + "Is [" + topic.lower() + "] related to medicine?"
	response = openai.Completion.create(model = "text-davinci-003", prompt = prompt, temperature = 0, max_tokens = 4)

	medical_topic = response.choices[0].text.strip()

	if medical_topic == "yes":
		return True
	else:
		return False

def generate_cards(topic, num):
	example_1 = "wiskott-aldrich -> Patients with Wiskott-Aldrich syndrome may present early with {{c1::petechiae}} and bleeding from the {{c2::umbilicus}} after separation\n\n"
	example_2 = "malabsorption -> Celiac disease in {{c1::adults}} classically presents with chronic steatorrhea and bloating\n\n"
	example_3 = "infectious disease -> HSV encephalitis is diagnosed using {{c1::PCR of CSF}}\n\n"
	example_4 = "neurology -> Intracranial {{c1::MR venography}} is used to visualize the dural venous sinuses and diagnose {{c2::cerebral sinus thrombosis}}\n\n"
	example_5 = "illicit drugs -> In severe cases, {{c1::PCP}} intoxication can cause {{c2::seizures}}, encephalopathy, or a comatose state\n\n"
	example_6 = "herpes encephalitis -> HSV-1 commonly spreads to the CNS from the {{c1::oropharynx}} via the {{c2::trigeminal}} nerve or is reactivated from {{c3::latent HSV-1 infection}}\n\n"
	example_7 = "vitamin b12 -> {{c1::Vitamin B12}} deficiency most commonly occurs in the context of {{c2::veganism}}, {{c3::pernicious}} anemia, and {{c4::Crohn disease}}\n\n"
	example_8 = "stroke -> Strokes typically present with the onset of focal neurologic deficits over {{c1::minutes to hours}}\n\n"

	examples = example_1 + example_2 + example_3 + example_4 + example_5 + example_6 + example_7 + example_8

	cards = []

	facts = openai.Completion.create(model = "text-davinci-003", prompt = examples + topic.lower() + " ->", temperature = 0.96, max_tokens = 72, n = num, presence_penalty = 1.4, frequency_penalty = 1.4, stop = "\n\n")

	cut_short = 0

	for i in range(num):
		fact = facts.choices[i].text.strip()

		if facts.choices[i].finish_reason == "length":
			cut_short += 1
		else:
			cards.append(fact)

	while cut_short > 0:
		facts = openai.Completion.create(model = "text-davinci-003", prompt = examples + topic.lower() + " ->", temperature = 0.96, max_tokens = 72, n = cut_short, presence_penalty = 1.4, frequency_penalty = 1.4, stop = "\n\n")

		inner_cut_short = 0

		for i in range(cut_short):
			fact = facts.choices[i].text.strip()

			if facts.choices[i].finish_reason == "length":
				inner_cut_short += 1
			else:
				cards.append(fact)

		cut_short = inner_cut_short

	return cards
