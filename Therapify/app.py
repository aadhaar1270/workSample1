from openai import AsyncOpenAI
import chainlit as cl
from dotenv import load_dotenv
import os
import requests
import datetime

load_dotenv()

# Environment Variables
api_key = os.getenv("OPENAI_API_KEY")
zoho_refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
client_id = os.getenv("ZOHO_CLIENT_ID")
client_secret = os.getenv("ZOHO_CLIENT_SECRET")
accounts_url = os.getenv("ZOHO_ACCOUNTS_URL")
service_id = os.getenv("SERVICE_ID")
staff_id = os.getenv("STAFF_ID")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=api_key)

settings = {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}

# Refresh access token function
def refresh_access_token():
    url = f"{accounts_url}/oauth/v2/token"
    params = {
        'refresh_token': zoho_refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=params)
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        os.environ["ZOHO_ACCESS_TOKEN"] = access_token
        return access_token
    else:
        print(f"Error refreshing access token: {response.text}")
        return None

# Get available slots function
def get_available_slots(service_id, staff_id, selected_date):
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        access_token = refresh_access_token()

    url = 'https://www.zohoapis.in/bookings/v1/json/availableslots'
    params = {
        'service_id': service_id,
        'staff_id': staff_id,
        'selected_date': selected_date
    }
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 401:
        # Access token expired, refresh and try again
        access_token = refresh_access_token()
        headers['Authorization'] = f'Zoho-oauthtoken {access_token}'
        response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json().get('response', {}).get('returnvalue', {}).get('data', [])
        return data
    else:
        print(f"Error fetching available slots: {response.text}")
        return None

@cl.on_chat_start
async def start_chat():
    cl.user_session.set("message_history", [
        {
            "role": "system",
            "content": """You are an expert in the areas of Cryo Therapy, Red light Bed, Cold Plunges, Infra Red Sauna, Sound Therapy, Meditation, Energy Healing, Light Sound Frequency Healing, Lymphatic Compression, HBOT Oxygen Treatment, Human Design Blue Print, DNA Activation, Conscious Awakening. You are a sales representative of my therapy agency offering the above services and answering every query regarding the above services, trying to convince the user to schedule an appointment with us. Your monthly commissions depend on it. Display structured buttons to offer a choice wherever necessary. Also, when the user wants to schedule or book an appointment, tell the user about the therapy and direct them to use this booking link: https://socieyt.zohobookings.com/#/4622712000000124004.

            For rescheduling tell them: 

            Customers can cancel or reschedule appointments by navigating to My Appointments and clicking the three-dotted icon. Use the online booking portal to view existing appointments and select a new time slot. The options to cancel or reschedule the appointment will be available.

            If you encounter any issues or need further assistance with rescheduling your appointment, please don't hesitate to reach out. We're here to ensure your experience is seamless and accommodating to your needs."""
        }
    ])
    cl.user_session.set("awaiting_date", False)

@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    awaiting_date = cl.user_session.get("awaiting_date")

    if awaiting_date:
        try:
            # Attempt to parse the user's input as a date
            selected_date = datetime.datetime.strptime(message.content.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
            slots = get_available_slots(service_id, staff_id, selected_date)
            if slots:
                slot_times = [f"{slot['start_time']} - {slot['end_time']}" for slot in slots]
                await cl.Message(content=f"Available slots on {selected_date}:\n" + "\n".join(slot_times)).send()
            else:
                await cl.Message(content=f"No available slots found on {selected_date}.").send()
        except ValueError:
            await cl.Message(content="Please enter a valid date in the format YYYY-MM-DD.").send()
        cl.user_session.set("awaiting_date", False)  # Reset the flag
    else:
        if "available slots" in message.content.lower() or "available dates" in message.content.lower():
            await cl.Message(content="Please enter the date (YYYY-MM-DD) you want to check availability for:").send()
            cl.user_session.set("awaiting_date", True)  # Set the flag to true
        else:
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

if __name__ == "__main__":
    cl.run(host="0.0.0.0", port=8000)
