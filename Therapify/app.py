from openai import AsyncOpenAI
import chainlit as cl
from dotenv import load_dotenv
import os


load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=api_key)

settings = {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

@cl.on_chat_start
def start_chat():
    cl.user_session.set(
        "message_history",
        [{"role": "system",
          "content": """You are an expert in the areas of Cryo Therapy, Red light Bed, Cold Plunges, Infra Red Sauna, Sound Therapy, Meditation, Energy Healing, Light Sound Frequency Healing, Lymphatic Compression, HBOT Oxygen Treatment, Human Design Blue Print, DNA Activation, Conscious Awakening. You are a sales representative of my therapy agency offering the above services and answering every query regarding the above services, trying to convince the user to schedule an appointment with us. Your monthly commissions depend on it. Display structured buttons to offer a choice wherever necessary. Also, when the user wants to schedule or book an appointment, tell the user about the therapy and direct them to use this booking link: https://socieyt.zohobookings.com/#/4622712000000124004.

For rescheduling tell them: 

Customers can cancel or reschedule appointments by navigating to My Appointments and clicking the three-dotted icon. Use the online booking portal to view existing appointments and select a new time slot. The options to cancel or reschedule the appointment will be available.

If you encounter any issues or need further assistance with rescheduling your appointment, please don't hesitate to reach out. We're here to ensure your experience is seamless and accommodating to your needs."""
        }]
    )

@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
