"""
    ___ DISCORD WEBHOOK ___
    Sends a message via discord's webhook API as embeds.

    __ HOW TO USE __
    In your .env file, create or modify the WEBHOOKS variable to match: '{"Discord": "https://discord.com/api/webhooks/<CHANNEL>/<AUTHORIZATION>"}'

    __ WARNING __
    Currently as it stands, it does not handle the webhook request limit.
    If your integrations create too many alerts, the requests will fail and you will not receive the alert.
    For more information, see https://discord.com/developers/docs/topics/rate-limits#header-format
    Valid response headers:
     - X-RateLimit-Limit - The number of requests that can be made
     - X-RateLimit-Remaining - The number of remaining requests that can be made
     - X-RateLimit-Reset - Epoch time (seconds since 00:00:00 UTC on January 1, 1970) at which the rate limit resets
     - X-RateLimit-Reset-After - Total time (in seconds) of when the current rate limit bucket will reset. Can have decimals to match previous millisecond ratelimit precision
     - X-RateLimit-Bucket - A unique string denoting the rate limit being encountered (non-inclusive of top-level resources in the path)
     - X-RateLimit-Global - Returned only on HTTP 429 responses if the rate limit encountered is the global rate limit (not per-route)
     - X-RateLimit-Scope - Returned only on HTTP 429 responses. Value can be user (per bot or user limit), global (per bot or user global limit), or shared (per resource limit)
    Exceeding rate limit body:
     - message: str # A message saying you are being rate limited.
     - retry_after: float # The number of seconds to wait before submitting another request.
     - 
"""

#region PUBLIC IMPORTS
import requests
import json
from datetime import datetime
#endregion

#region LOCAL IMPORTS
from .utilities.GLOBAL import WEBHOOKS, HOSTNAME, HOSTURL
#endregion

#region CONSTANTS
ALERTLEVEL = 0 # What level does the message need to be above (NOT inclusive) to raise an alert?

RED     = "15681391"
YELLOW  = "16765286"
GREEN   = "00448160"
BLUE    = "01149618"
GRAY    = "00473932"

DISCORDWEBHOOK = WEBHOOKS['Discord']
#endregion

#region CLASSES
class Field:
  def __init__(self, name: str, value: str, inline: bool):
    self.name: str = name
    self.value: str = value
    self.inline: bool = inline

  def getObject(self) -> dict:
    return {
      'name': self.name,
      'value': self.value,
      'inline': self.inline
    }

class Author:
  def __init__(self,
    name: str,
    url: str|None = None,
    icon_url: str|None = None,
    proxy_icon_url: str|None = None):

    self.name: str = name
    self.url: str|None = url
    self.icon_url: str|None = icon_url
    self.proxy_icon_url: str|None = proxy_icon_url
  
  def getObject(self) -> dict:
    data = {'name': self.name}
    if self.url: data['url'] = "https://" + self.url
    if self.icon_url: data['icon_url'] = "https://" + self.icon_url
    if self.proxy_icon_url: data['proxy_icon_url'] = "https://" + self.proxy_icon_url
    return data

class Embed:
  def __init__(self,
    title: str,
    description: str,
    color: str,
    fields: list[Field],
    timestamp: str,
    author: Author
    ):

    self.title: str = title
    self.description: str = description
    self.color: str = color
    self.fields: list[Field] = fields
    self.timestamp: str = timestamp
    self.author: Author = author

  def getObject(self) -> dict:
    content = {
      'title': self.title,
      'description': self.description,
      'color': self.color,
      'author': self.author.getObject(),
      'timestamp': self.timestamp
    }
    fields_list = []
    for field in self.fields:
      fields_list.append(field.getObject())
    if len(fields_list) > 0: content['fields'] = fields_list
    return content
#endregion

class Discord_Webhook:
  def __init__(self): pass

  def add_embeds_from_dict(self, timestamp: int, dictionary: dict) -> list[Embed]:
    embeds = []
    embed = Embed(
      title='',
      description='```yaml\n',
      color=GRAY,
      fields=[],
      timestamp=timestamp,
      author=Author(
        name=HOSTNAME,
        url=HOSTURL
      )
    )

    for key, value in dictionary.items():
      # Restrict key to a maximum of 256
      message = f"\n\"{key[:256]}\": {value}"
      # If embed is too large, end early. This is due to the fact that discord has a request limit of 6000 in TOTAL,
      #  and 4096 per embed.
      if 4096 < len(embed.description + message + '\n```'):
        # If too many embeds with too much data, replace with "and more"
        embed.description = embed.description[:4092] + "..."
        break
      # Else ... Add to embed
      embed.description += message

    # Final add embed
    embed.description += '\n```'
    embeds.append(embed)

    return embeds

  def generate_message(self, embeds: list[Embed]) -> str:
    embeds_json = []
    for embed in embeds[:10]:
        embeds_json.append(embed.getObject())

    return json.dumps({"embeds": embeds_json})

  def generate_payload(self, dictionary: dict) -> str:
    embeds = [Embed(
      title=dictionary['title'],
      description=dictionary['description'],
      color=[GRAY, BLUE, GREEN, YELLOW, RED, RED, RED][dictionary['severity']],
      fields=[],
      timestamp=dictionary['timestamp'].isoformat(),
      author=Author(
        name=HOSTNAME,
        url=HOSTURL
      )
    )]
    
    if 'json' in dictionary.keys(): embeds += self.add_embeds_from_dict(dictionary['timestamp'].isoformat(), dictionary['json'])
    
    return self.generate_message(embeds)

  def send_message(self, message: dict):
    # Don't send debugging 
    if message['severity'] <= ALERTLEVEL: return None

    # Generate payload
    payload = self.generate_payload(message)

    headers = {'content-type': 'application/json', 'accept-charset': 'UTF-8'}
    response = requests.post(DISCORDWEBHOOK, data=payload, headers=headers)
    if response.status_code != 204:
      return Exception(f"Status code: {response.status_code} Text: {response.text}")
      requests.post(
        url=DISCORDWEBHOOK,
        data=generate_message([
          Embed(
            title=f":x: {response.status_code}",
            description=f"```json\n{response.text}```",
            color=RED,
            fields=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            author=Author(
              name=HOSTNAME,
              url=HOSTURL
            )
          )
        ]),
        headers=headers
        )
    return response