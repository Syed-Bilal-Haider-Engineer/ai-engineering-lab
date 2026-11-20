from openai import OpenAI
system_one_prompt = "English: Dog → Spanish: Perro. "

client = OpenAI(
   api_key="",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
   messages=[
        {"role": "system", "content": system_one_prompt},
        {"role": "user", "content": "Now translate 'Cow' to Spanish."},
    ]
)

print(response.choices[0].message.content)
