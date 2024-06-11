import logging
import json
import os
from hotel_ai.utils.prompt import system_prompt
from hotel_ai.functions.functions import (
    check_availability,
    book_room,
    check_in_room,
    check_out_room,
    auto_check_out
)
from openai import OpenAI

TOKEN = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=TOKEN)

user_contexts = {}


# Пример использования


def run_conversation(user_id, content):
    if user_id not in user_contexts:
        user_contexts[user_id] = [{"role": "system", "content": system_prompt}, {"role": "user", "content": content}]
    else:
        user_contexts[user_id].append({"role": "user", "content": content})
    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check availability of rooms",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "The path to the Excel file"},
                        "room_type": {"type": "string",
                                      "description": "The type of the room (e.g., 'Single', 'Double', 'Lux')"},
                        "date": {"type": "string", "description": "The date for which availability is being checked"}
                    },
                    "required": ["file_path", "room_type", "date"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "book_room",
                "description": "Book a room",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "The path to the Excel file"},
                        "room": {"type": "string", "description": "The room to book"},
                        "date": {"type": "string", "description": "The date for the booking"},
                        "guest_name": {"type": "string", "description": "The name of the guest"}
                    },
                    "required": ["file_path", "room", "date", "guest_name"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_in_room",
                "description": "Check in a guest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "The path to the Excel file"},
                        "booking_id": {"type": "string", "description": "The unique ID of the booking"},
                        "date": {"type": "string", "description": "The date for the check-in"}
                    },
                    "required": ["file_path", "booking_id", "date"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_out_room",
                "description": "Check out a guest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "The path to the Excel file"},
                        "booking_id": {"type": "string", "description": "The unique ID of the booking"}
                    },
                    "required": ["file_path", "booking_id"],
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "auto_check_out",
                "description": "Auto check out guests",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "The path to the Excel file"}
                    },
                    "required": ["file_path"],
                },
            }
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=user_contexts[user_id],
            tools=tools,
            tool_choice="auto",
            temperature=0.5
        )
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        return None

    if response and response.choices:
        response_message = response.choices[0].message
        user_contexts[user_id].append(response_message)
        tool_calls = response_message.tool_calls

        if tool_calls:
            available_functions = {
                "check_availability": check_availability,
                "book_room": book_room,
                "check_in_room": check_in_room,
                "check_out_room": check_out_room,
                "auto_check_out": auto_check_out,
            }
            for tool_call in tool_calls:
                logging.info(f"Function: {tool_call.function.name}")
                logging.info(f"Params: {tool_call.function.arguments}")
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                logging.info(f"API: {function_response}")
                user_contexts[user_id].append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

            second_response = client.chat.completions.create(
                temperature=0.5,
                model="gpt-4o",
                messages=user_contexts[user_id],
                stream=False

            )
            return second_response
    return response
