import asyncio
import concurrent.futures
import functools
import io
import json

import discord
from PIL import Image, ImageDraw, ImageSequence
from discord.ext import commands


LARGE_DIAMETER = 110
SMALL_DIAMETER = 80

# Two masks, one for the normal size, and a smaller one for the final stage of the bonk
LARGE_MASK = Image.new("L", (LARGE_DIAMETER,) * 2)
draw = ImageDraw.Draw(LARGE_MASK)
draw.ellipse((0, 0, LARGE_DIAMETER, LARGE_DIAMETER), fill=255)

SMALL_MASK = Image.new("L", (SMALL_DIAMETER,) * 2)
draw = ImageDraw.Draw(SMALL_MASK)
draw.ellipse((0, 0, SMALL_DIAMETER, SMALL_DIAMETER), fill=255)

BONK_GIF = Image.open("bot/resources/images/yodabonk.gif")
with open("bot/resources/yodabonk.json") as f:
    GIF_DETAILS = json.load(f)

PFP_ENTRY_FRAME = GIF_DETAILS["PFP_ENTRY_FRAME"]
BONK_FRAME = GIF_DETAILS["BONK_FRAME"]
PFP_EXIT_FRAME = GIF_DETAILS["PFP_EXIT_FRAME"]
PFP_CENTRE = GIF_DETAILS["PFP_CENTRE"]


class Bonk(commands.Cog):
    """Cog for sending bonking gifs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _generate_gif(pfp: bytes) -> None:
        pfp = Image.open(io.BytesIO(pfp))
        pfps = [pfp.resize((LARGE_DIAMETER,) * 2), pfp.resize((SMALL_DIAMETER,) * 2)]

        out_images = []

        for i, frame in enumerate(ImageSequence.Iterator(BONK_GIF)):

            canvas = Image.new("RGBA", BONK_GIF.size)
            canvas.paste(frame.convert("RGBA"), (0, 0))

            if PFP_ENTRY_FRAME <= i <= PFP_EXIT_FRAME:
                if i == BONK_FRAME:
                    canvas.paste(
                        pfps[1],
                        (
                            PFP_CENTRE[0] - SMALL_DIAMETER // 2,
                            PFP_CENTRE[1]
                            - SMALL_DIAMETER // 2
                            + 10,  # Shift avatar down by 10 px in the bonk frame
                        ),
                        SMALL_MASK,
                    )
                else:
                    canvas.paste(
                        pfps[0],
                        (
                            PFP_CENTRE[0] - LARGE_DIAMETER // 2,
                            PFP_CENTRE[1] - LARGE_DIAMETER // 2,
                        ),
                        LARGE_MASK,
                    )

            out_images.append(canvas)

        out_images[0].save(
            "out.gif",
            "GIF",
            save_all=True,
            append_images=out_images[1:],
            loop=0,
            duration=50,
        )

    @commands.command()
    async def bonk(self, ctx: commands.Context, member: discord.Member) -> None:
        """Command to send gif of mentioned member being bonked."""
        pfp = await member.avatar_url.read()
        func = functools.partial(self._generate_gif, pfp)
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await asyncio.get_running_loop().run_in_executor(pool, func)
        await ctx.send(file=discord.File("out.gif"))


def setup(bot: commands.Bot) -> None:
    """Load the Bonk cog."""
    bot.add_cog(Bonk(bot))
