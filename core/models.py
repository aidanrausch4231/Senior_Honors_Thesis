import anthropic 
class Model:
    def __init__(self, apiKey: str):
        self.apiKey = apiKey

    def changeKey(self, key):
        self.apiKey = key
    
    @property
    def client(self):
        raise NotImplementedError

#class local(Model):


class Claude(Model):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        super().__init__(api_key)
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def call(self, messages: list, system: str = "", tools: list = None, max_tokens: int = 4096):
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages
        )
        if tools:
            kwargs["tools"] = tools
        return self._client.messages.create(**kwargs)







