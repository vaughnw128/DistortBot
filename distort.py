import discord, logging, json
from discord.ext import commands
from config import token, guild
from wand.image import Image
import urllib
import requests
import os
import imghdr

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

logging.basicConfig(level=logging.WARNING)

image_types = ["png", "jpeg", "gif", "jpg"]

async def image_handler(ctx, img):
	if img is not None:
		try:
			response = requests.get(img)
			fname = requests.utils.urlparse(img)
			fname=os.path.basename(fname.path)
			print(fname)
			req = urllib.request.Request(img, headers={'User-Agent': 'Mozilla/5.0'})
			with open(fname, "wb") as f:
				with urllib.request.urlopen(req) as r:
					f.write(r.read())
		except requests.ConnectionError as exception:
			await ctx.channel.send("You have entered an invalid URL")
			return None
		except requests.HTTPError as exception:
			await ctx.channel.send("You have entered an invalid URL")
			return None
	else:
		if ctx.message.attachments:
			for attachment in ctx.message.attachments:
				if any(attachment.filename.lower().endswith(image) for image in image_types):
					await attachment.save(attachment.filename)
					fname=str(attachment.filename)
		else:
			await ctx.channel.send("Please attach an image")
			return None

	return fname

@bot.event
async def on_ready():
    print('Bot is ready for use')

@bot.command(name="distort", pass_context=True)
async def distort(ctx, img: str=None):
	fname = await image_handler(ctx,img)
	await ctx.message.delete()
	
	if(imghdr.what(fname)=='gif'):
		with Image(filename=fname) as img:
			with Image(width=round(img.width*.60), height=round(img.height*.60)) as new:
				for _, frame in enumerate(img.sequence):
					frame.liquid_rescale(round(img.width*.60), round(img.height*.60))
					new.sequence.append(frame)
				#for cursor in range(len(new.sequence)):
				#	with new.sequence[cursor] as frame:
				#		frame.delay = 10 * (cursor + 1)
				for _, frame in enumerate(img.sequence):
					print(frame)

				new.type = 'optimize'
				new.save(filename=fname)
				await ctx.send(file=discord.File(fname))

	else:
		with Image(filename=fname) as img:
			img.liquid_rescale(round(img.width*.60), round(img.height*.60))
			img.save(filename=fname)
			await ctx.send(file=discord.File(fname))
	

if __name__ == '__main__':
	bot.run(token)
