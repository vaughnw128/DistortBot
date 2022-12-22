# Distort Bot
# Distorts images and gifs in discord
# Made by Vaughn Woerpel
import discord
from config import token, apikey, guild
from wand.image import Image
from discord import app_commands
import urllib
import requests
import os
import validators

MY_GUILD = discord.Object(id=int(guild))

# Method used to grab images from messages. It can grab images from embeds, and normal message attachments. Grabs and validates the links.
async def grab_img(message):
	# Valid image types
	types = ["png", "jpg", "jpeg", "gif", "mp4"]
	url = ""
	# Gets the image URL using various means
	# First checks the embed class
	if message.embeds:
		# Checks if the embed itself is an image and grabs the url
		if message.embeds[0].url is not None:
			url = message.embeds[0].url
		# Checks if the embed is a video (tenor gif) and grabs the url
		elif message.embeds[0].video.url is not None:
			url = message.embeds[0].video.url
	# Checks to see if the image is a message attachment
	elif message.attachments:
		url = message.attachments[0].url
	# Validates the URLs
	else:
		for item in message.content.split(' '):
			if validators.url(item):
				url = item
	# Remove the trailing modifiers at the end of the link
	url = url.partition("?")[0]
	# Passes off tenor gif
	if "tenor" in url:
		q = url.split("/")[len(url.split("/"))-1]
		# Returns as a dict
		resp = requests.get(f"https://tenor.googleapis.com/v2/search?key={apikey}&q={q}&limit=1")
		data = resp.json()

		url = data['results'][0]['media_formats']['mediumgif']['url']
	# Quickly check the filetype of the URL
	if not url.endswith(tuple(types)):
		return None
	# We can proceed as long as it is a valid URL
	if validators.url(url):
		fname = requests.utils.urlparse(url)
		fname = f"images/{os.path.basename(fname.path)}"
		req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
		with open(fname, "wb") as f:
			with urllib.request.urlopen(req) as r:
				f.write(r.read())
		
		return fname

async def distort(fname):
	if fname is not None:
		# Handles distorting the gif
		if fname.endswith('gif'):
			with Image(filename=fname) as temp_img:
				with Image(width=round(temp_img.width*.60), height=round(temp_img.height*.60)) as new:
					for _, frame in enumerate(temp_img.sequence):
						frame.liquid_rescale(round(temp_img.width*.60), round(temp_img.height*.60))
						new.sequence.append(frame)
					new.type = 'optimize'
					new.save(filename=fname)
					return fname
		# Handles distorting the photo
		else:
			with Image(filename=fname) as temp_img:
				temp_img.liquid_rescale(round(temp_img.width*.60), round(temp_img.height*.60))
				temp_img.save(filename=fname)
				return fname

# Defining the distortclient class with all of the command trees		
class DistortClient(discord.Client):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.tree = app_commands.CommandTree(self)

	async def setup_hook(self) -> None:
		self.tree.copy_global_to(guild=MY_GUILD)
		await self.tree.sync(guild=MY_GUILD)

	async def on_ready(self):
		print('Bot ready!')
		print(self.user.name)
		print('------------')

# View setup for the buttons
class DistortView(discord.ui.View):
	@discord.ui.button(label="Distort", style=discord.ButtonStyle.green)
	async def distort_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		fname = await grab_img(interaction.message)
		distorted = await distort(fname)
		await interaction.message.edit(attachments=[discord.File(distorted)])
		await interaction.response.defer()

# Defines the client and the client intents
intents = discord.Intents.default()
intents.message_content = True
client = DistortClient(intents=intents)

# Checking to see if online through pinpong command
@client.tree.command()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# Context tree command for the distort command.
@client.tree.context_menu(name = "Distort", guild = MY_GUILD)
async def distort_context_menu(interaction: discord.Interaction, message: discord.Message):
	fname = await grab_img(message) # Grabs the image
	distorted = await distort(fname)
	await interaction.response.send_message(file=discord.File(distorted), view=DistortView(timeout=None))

client.run(token)