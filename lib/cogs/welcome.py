from discord import Forbidden
from discord.ext.commands import Cog
from discord.ext.commands import command

from ..db import db

class Welcome(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("welcome")

	@Cog.listener()
	async def on_member_join(self, member):
		db.execute("INSERT INTO exp (UserID) VALUES (?)", member.id)
		await self.bot.get_channel(790255278481997874).send(f"Hey Optic {member.mention}, welcome to **{member.guild.name}**!")

		try:
			await member.send(f"Hey Optic {member.mention}, welcome to **{member.guild.name}**!")

		except Forbidden:
			pass

		#await member.add_roles(*(member.guild.get_role(id_) for id_ in(paste the role id_ here)))

	@Cog.listener()
	async def on_member_remove(self, member):
		db.execute("DELETE FROM exp WHERE UserID = ?", member.id)
		await self.bot.get_channel(798985078255648798).send(f"Optic {member.display_name} has just left the server :sob:")


def setup(bot):
	bot.add_cog(Welcome(bot))