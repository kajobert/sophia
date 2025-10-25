
import asyncio
import websockets

async def test_chat():
    uri = "ws://127.0.0.1:8000/ws/e2e_test"
    async with websockets.connect(uri) as websocket:
        print(">>> Connected to WebSocket.")

        # Send a message to Sophia
        message_to_send = "Hello Sophia, please tell me the capital of France in a single word."
        print(f">>> You: {message_to_send}")
        await websocket.send(message_to_send)

        # Wait for and print the response
        response = await websocket.recv()
        print(f"<<< Sophia: {response}")

if __name__ == "__main__":
    asyncio.run(test_chat())
