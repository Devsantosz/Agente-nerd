from database import iniciar_banco
from interface import ChatInterface


iniciar_banco()


app = ChatInterface()

app.mainloop()