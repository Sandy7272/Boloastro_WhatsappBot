from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from backend.flows.main_flow import handle_message

app = FastAPI()

@app.post("/bot")
async def bot(request: Request):
    form = await request.form()

    phone = form.get("From")
    msg = form.get("Body")

    print("RAW DATA:", form)
    print("PHONE:", phone)
    print("MESSAGE:", msg)

    reply = handle_message(phone, msg)
    print("REPLY:", reply)

    resp = MessagingResponse()
    resp.message(reply)

    # 🔥 IMPORTANT: return XML response
    return Response(
        content=str(resp),
        media_type="text/xml"
    )
