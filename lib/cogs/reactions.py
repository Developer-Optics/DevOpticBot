from datetime import datetime, timedelta
from random import choice

from discord import Embed
from discord.ext.commands import Cog
from discord.ext.commands import command, has_permissions

from ..db import db

pings = {
	"📢": 790918678899064833, # Announcement Ping 
	"📃": 801404701248585750, # QOTD Ping




}

# Here are all the number emotes.
# 0⃣ 1️⃣ 2⃣ 3⃣ 4⃣ 5⃣ 6⃣ 7⃣ 8⃣ 9⃣

numbers = ("1️⃣", "2⃣", "3⃣", "4⃣", "5⃣",
		   "6⃣", "7⃣", "8⃣", "9⃣", "🔟")


class Reactions(Cog):
	def __init__(self, bot):
		self.bot = bot
		self.polls = []

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.reaction_message = await self.bot.get_channel(859879812204986388).fetch_message(1061356967630733422)
			self.starboard_channel = self.bot.get_channel(801422018318696478)
			self.bot.cogs_ready.ready_up("reactions")

	@command(name="createpoll", aliases=["mkpoll"])
	@has_permissions(manage_guild=True)
	async def create_poll(self, ctx, hours: int, question: str, *options):
		if len(options) > 10:
			await ctx.send("You can only supply a maximum of 10 options.")

		else:
			embed = Embed(title="Poll",
						  description=question,
						  colour=ctx.author.colour,
						  timestamp=datetime.utcnow())

			fields = [("Options", "\n".join([f"{numbers[idx]} {option}" for idx, option in enumerate(options)]), False),
					  ("Instructions", "React to cast a vote!", False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			message = await ctx.send(embed=embed)

			for emoji in numbers[:len(options)]:
				await message.add_reaction(emoji)

			self.polls.append((message.channel.id, message.id))

			self.bot.scheduler.add_job(self.complete_poll, "date", run_date=datetime.now()+timedelta(seconds=hours),
									   args=[message.channel.id, message.id])

	async def complete_poll(self, channel_id, message_id):
		message = await self.bot.get_channel(channel_id).fetch_message(message_id)

		most_voted = max(message.reactions, key=lambda r: r.count)

		await message.channel.send(f"The results are in and option {most_voted.emoji} was the most popular with {most_voted.count-1:,} votes!")
		self.polls.remove((message.channel.id, message.id))

	@Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if self.bot.ready and payload.message_id == self.reaction_message.id:
			role = self.bot.guild.get_role(pings[payload.emoji.name])
			await payload.member.add_roles(role, reason = "Ping role reaction.")

		elif payload.message_id in (poll[1] for poll in self.polls):
			message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

			for reaction in message.reactions:
				if (not payload.member.bot
					and payload.member in await reaction.users().flatten()
					and reaction.emoji != payload.emoji.name):
					await message.remove_reaction(reaction.emoji, payload.member)

		elif payload.emoji.name == "⭐":
			message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

			if not message.author.bot and payload.member.id != message.author.id:
				msg_id, stars = db.record("SELECT StarMessageID, Stars FROM starboard WHERE RootMessageID = ?",
										  message.id) or (None, 0)

				embed = Embed(title="Starred message",
							  colour=message.author.colour,
							  timestamp=datetime.utcnow())

				fields = [("Author", message.author.mention, False),
						  ("Content", message.content or "See attachment", False),
						  ("Stars", stars+1, False)]

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				if len(message.attachments):
					embed.set_image(url=message.attachments[0].url)

				if not stars:
					star_message = await self.starboard_channel.send(embed=embed)
					db.execute("INSERT INTO starboard (RootMessageID, StarMessageID) VALUES (?, ?)",
							   message.id, star_message.id)

				else:
					star_message = await self.starboard_channel.fetch_message(msg_id)
					await star_message.edit(embed=embed)
					db.execute("UPDATE starboard SET Stars = Stars + 1 WHERE RootMessageID = ?", message.id)

			else:
				await message.remove_reaction(payload.emoji, payload.member)

	@Cog.listener()
	async def on_raw_reaction_remove(self, payload):
		if self.bot.ready and payload.message_id == self.reaction_message.id:
			member = self.bot.guild.get_member(payload.user_id)
			role = self.bot.guild.get_role(pings[payload.emoji.name])
			await member.remove_roles(role, reason = "Ping role reaction.")


def setup(bot):
	bot.add_cog(Reactions(bot))