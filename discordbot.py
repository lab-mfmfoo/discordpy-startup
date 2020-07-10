import discord
import os
from time import sleep
from random import shuffle, choice, randint, sample
from datetime import datetime

trans = str.maketrans({s:"" for s in " 　,./\\]:;@[\^-|~=)('&%$#\"!<>?_}*+`{"})

TOKEN = os.environ['DISCORD_BOT_TOKEN']

client = discord.Client()


@client.event
async def on_ready():
    print("ログインしました。")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    command = message.content.split(" ")[0]
    guild = message.guild
    if command == "!setup":
        for channel in guild.text_channels:
            if channel.name == "text_for_wordwolf":
                break
        else:
            overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            channel = await guild.create_text_channel(f"text_for_wordwolf", overwrites = overwrites)
            await channel.send("ここはワードウルフで使用する専用テキストチャンネルです。")
        
        for channel in guild.voice_channels:
            if channel.name == "voice_for_wordwolf":
                break
        else:
            channel = await guild.create_voice_channel(f"voice_for_wordwolf", overwrites = overwrites)
            await channel.send("ここはワードウルフで使用する専用ボイスチャンネルです。")
        
        await message.channel.send("セットアップが完了しました。")

    if command == "!teardown":
        
        for channel in guild.text_channels:
            if channel.name == "text_for_wordwolf":
                channel.delete()
                break
            
        for channel in guild.voice_channels:
            if channel.name == "voice_for_wordwolf":
                channel.delete()
                break
            
        await message.channel.send("ティアダウンが完了しました。")
    
    if command == "!startGame":
        
        for channel in guild.text_channels:
            if channel.name == "ゲーム用":
                text_channel = channel
                break
        else:
            await message.channel.send("セットアップコマンド !setup を実行して下さい。")
            return
        
        for channel in guild.voice_channels:
            if channel.name == "ゲーム用":
                voice_channel = channel
                break
        else:
            await message.channel.send("セットアップコマンド !setup を実行して下さい。")
            return
        
        
        players = [player for player in voice_channel.members]
        players.sort(key=lambda x:x.display_name)
        
        params = message.content.split(" ")[1:]
        timelimit = 45*(len(players)+1)
        if "-t" in params:
            try:
                timelimit = int(params[params.index("-t")+1])
                if timelimit < 180:
                    await message.channel.send("**制限時間は 180 秒以上を設定して下さい。**")
                    return
            except Exception:
                await message.channel.send("**制限時間の値が不正です。必ず数値で入力して下さい。**")
                return
        nWolf = 1
        rMode = False
        if "-w" in params:
            try:
                tmp = params[params.index("-w")+1]
                if tmp == "r":
                    nWolf = randint(1, (len(players)-1)//2)
                    rMode = True
                else:
                    nWolf = int(tmp)
                    if nWolf == 0:
                        await message.channel.send("**ウルフの人数は 1 人以上を設定して下さい。**")
                        return 
            except Exception:
                await message.channel.send("**ウルフの人数の値が不正です。必ず数値で入力して下さい。**")
                return
            
        inversion = False
        if "-i" in params:
            inversion = True
        if nWolf > 1:
            await message.channel.send("**現在ウルフの人数が2人以上には対応していません。**")
            return
        
        nVillager = len(players) - nWolf
        if nVillager <= nWolf:
            await message.channel.send("**村人の人数 > ウルフの人数 となるように設定してください。**")
            return

        filename = r"D:\PythonScript\wordwolf\お題2.csv" if "-s" in params else r"D:\PythonScript\wordwolf\お題.csv"
        
        
        with open(filename, "r", encoding="utf-8") as f:
            if "-r" in params:
                junle = "ランダム"
                words = set()
                for line in f:
                    theme = line.strip().split(",")
                    for word in theme[1:]:
                        if word != "":
                            words.add(word)
                        else:
                            break
                villager_word, wolf_word = sample(words, 2)
            else:
                theme = choice(f.readlines()).strip().split(",")
                junle = theme[0]
                if "" in theme:
                    words = theme[1:theme.index("")]
                else:
                    words = theme[1:]
                villager_word, wolf_word = sample(words, 2)
        
        isWolf = [True]*nWolf + [False]*nVillager
        
        shuffle(isWolf)
        W = isWolf.index(True)
        
        vote_channels = []
        
        
        for i, member in enumerate(players):
            overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    member:discord.PermissionOverwrite(read_messages=True, send_messages=False)
            }
            channel = await guild.create_text_channel(f"投票（{member.display_name.lower().translate(trans)}）", overwrites = overwrites)
            await channel.send(f"あなたのお題は **{wolf_word if isWolf[i] else villager_word }** です。")
            vote_channels.append(channel)
                
            await text_channel.set_permissions(member, read_messages=True, send_messages=True)
        try:
            now = datetime.now().strftime('%Y/%m/%d %H:%M')
            start_texts = [
                    f"------------------------------------------------\n▼▼{now} ゲーム開始▼▼",
                    "\nお題を配布したので確認してください。",
                    f"制限時間は **{timelimit}** 秒です。",
                    "村人およびウルフの人数は秘密です。" if rMode else f"村人は**{nVillager}**人、ウルフは**{nWolf}**人です。",
                    "\n参加者は以下の通りです。",
                    *[player.display_name for player in players],
                    "\nそれではゲームをスタートします。"
            ]
            
            await text_channel.send("\n".join(start_texts))

            counter = 0
            for i in range(timelimit):
                sleep(1)
                if (timelimit - 10 <= i):
                    await text_channel.send("**残り 10 秒です。**")
                    sleep(10)
                    break
                elif (i >= timelimit*9/10 and counter == 2):
                    await text_channel.send(f"制限時間の 9 割が経過しました。残り **{timelimit - int(timelimit*9/10)}** 秒です。")
                    counter = 3
                elif (i >= timelimit*7/10 and counter == 1):
                    await text_channel.send(f"制限時間の 7 割が経過しました。残り **{timelimit - int(timelimit*7/10)}** 秒です。")
                    counter = 2
                elif (i >= timelimit/2 and counter == 0):
                    await text_channel.send(f"制限時間の 5 割が経過しました。残り **{timelimit - int(timelimit/2)}** 秒です。")
                    counter = 1
                if (i%5 == 0):
                    messages = await text_channel.history(limit=1).flatten()
                    last_message = messages[0]
                    if (last_message.content == "!endGame"):
                        break
                        
                    
            
            await text_channel.send(f"制限時間が経過しました。各自投票チャンネルで投票を行って下さい。")
            
            vote_text = "ウルフだと思う人を以下から**番号**で投票して下さい。\n**番号以外は決して入力しないで下さい。**\n"
            for i, member in enumerate(players):
                await text_channel.set_permissions(member, read_messages=True, send_messages=False)
                await vote_channels[i].send(vote_text + "\n".join([f"{j:2d}\t{member.display_name}" for j,member in enumerate(players[:i] + players[i+1:], start=1)]))
                await vote_channels[i].set_permissions(member, read_messages=True, send_messages=True)
                
                
            sleep(10)
                            
            votes = [None]*len(players)
            while True:
                nFinish = sum(1 for v in votes if v is not None)
                if nFinish == len(players):
                    break
                for i,member in enumerate(players):
                    if votes[i]:
                        continue
                    channel = vote_channels[i]
                    messages = await channel.history(limit=1).flatten()
                    last_message = messages[0]
                    if last_message.author.bot:
                        continue
                    num = last_message.content
                    try:
                        num = int(num)-1
                        if num >= i:
                            num += 1
                        if num < 0 or len(players) <= num:
                            await channel.send("範囲外の番号です。")
                        else:
                            votes[i] = num
                    except ValueError:
                        await channel.send("番号以外を入力しないでください。")
                sleep(3)
    
            # 最終結果取得
            for i,member in enumerate(players):
                channel = vote_channels[i]
                messages = await channel.history(limit=1).flatten()
                last_message = messages[0]
                if last_message.author.bot:
                    continue
                num = last_message.content
                try:
                    num = int(num)-1
                    if num >= i:
                        num += 1
                    if num < 0 or len(players) <= num:
                        continue
                    else:
                        votes[i] = num
                except ValueError:
                    pass
            voted = [(i,[]) for i in range(len(players))]
            for i,member in enumerate(players):
                voted[votes[i]][1].append(i)
            
            voted.sort(key=lambda x:-len(x[1]))
            max_voted = len(voted[0][1])
            max_members = [(i,_voted) for i,_voted in voted if len(_voted) == max_voted]
            
            loseWolf = True
            
            await text_channel.send("**【投票結果】**\n" + "\n".join([f"票数:{len(_voted):2d}\t{players[i].display_name}  ←  " + ", ".join(players[j].display_name for j in _voted) for i,_voted in voted if len(_voted)]) + "\n")
            if len(max_members) == 1:
                i = voted[0][0]
                if isWolf[i]:
                    await text_channel.send(f"**{players[i].display_name}** さんはウルフでした。**村人の勝利です！**")
                else:
                    await text_channel.send(f"{players[i].display_name} さんはウルフではありませんでした。\nウルフは **{players[W].display_name}** さんでした。**ウルフの勝利です！**")
                    loseWolf = False
            else:
                await text_channel.send("同率1位が複数いるため**決選投票**を行います。\n投票チャンネルにて再投票を行って下さい。\n変更がない場合は投票しなくてかまいません")
                        
                votes2 = [None] * len(players)
                idx_max_members = list(zip(*max_members))[0]
                for i,member in enumerate(players):
                    channel = vote_channels[i]
                    await channel.send(vote_text + "\n".join([f"{k:2d}\t{players[j].display_name}" for k, (j, _voted) in enumerate((_vote for _vote in max_members if i != _vote[0]), start=1)]))
                    if votes[i] in idx_max_members:
                        votes2[i] = idx_max_members.index(votes[i])
                
                if len(idx_max_members) == 2:
                    votes2[idx_max_members[0]] = 1
                    votes2[idx_max_members[1]] = 0
                
                sleep(20)
                while True:
                    nFinish = sum(1 for v in votes2 if v is not None)
                    if nFinish == len(players):
                        break
                    for i,member in enumerate(players):
                        if votes2[i]:
                            continue
                        channel = vote_channels[i]
                        messages = await channel.history(limit=1).flatten()
                        last_message = messages[0]
                        if last_message.author.bot:
                            continue
                        num = last_message.content
                        try:
                            num = int(num)-1
                            if i in idx_max_members:
                                if num >= idx_max_members.index(i):
                                    num += 1
                            if num < 0 or len(idx_max_members) <= num:
                                await channel.send("範囲外の番号です。")
                            else:
                                votes2[i] = num
                        except ValueError:
                            await channel.send("番号以外を入力しないでください。")
                    sleep(3)
                # 最終結果取得
                for i,member in enumerate(players):
                    channel = vote_channels[i]
                    messages = await channel.history(limit=1).flatten()
                    last_message = messages[0]
                    if last_message.author.bot:
                        continue
                    num = last_message.content
                    try:
                        num = int(num)-1
                        if i in idx_max_members:
                            if num >= idx_max_members.index(i):
                                num += 1
                        if num < 0 or len(idx_max_members) <= num:
                            continue
                        else:
                            votes2[i] = num
                    except ValueError:
                        pass
            
                voted2 = [(i,[]) for i in range(len(idx_max_members))]
                for i,member in enumerate(players):
                    voted2[votes2[i]][1].append(i)
                voted2.sort(key=lambda x:-len(x[1]))
                max_voted2 = len(voted2[0][1])
                max_members2 = [(i,_voted2) for i,_voted2 in voted2 if len(_voted2) == max_voted2]
                
                await text_channel.send("**【決選投票結果】**\n" + "\n".join([f"票数:{len(_voted):2d}\t{players[max_members[i][0]].display_name}  ←  " + ", ".join(players[j].display_name for j in _voted) for i,_voted in voted2 if len(_voted)]) + "\n")
                if len(max_members2) == 1:
                    i = max_members[voted2[0][0]][0]
                    if isWolf[i]:
                        await text_channel.send(f"**{players[i].display_name}** さんはウルフでした。**村人の勝利です！**")
                    else:
                        await text_channel.send(f"{players[i].display_name} さんはウルフではありませんでした。\nウルフは **{players[W]}** さんでした。**ウルフの勝利です！**")
                        loseWolf = False
                else:
                    I = [max_members[i][0] for i,_voted2 in max_members2]
                    if any(map(lambda i: isWolf[i], I)):
                        await text_channel.send(f"同率1位の中にウルフである **{players[W].display_name}** さんが含まれています。よって**引き分け**です。")
                    else:                
                        await text_channel.send(f"同率1位の中にウルフである **{players[W].display_name}** さんが含まれていません。よって**ウルフの勝利**です！")
                        loseWolf = False
                
            if loseWolf and inversion :
                await text_channel.send(f"\n**【逆転モード】**\nウルフの **{players[W].display_name}** さんは村人側の答えを予想して、ここに書き込んで下さい。\n制限時間は **60** 秒です。")
                await text_channel.set_permissions(players[W], read_messages=True, send_messages=True)
                
                answer = ""
                sleep(5)
                for i in range(11):
                    messages = await text_channel.history(limit=1).flatten()
                    last_message = messages[0]
                    if not(last_message.author.bot):
                        answer = last_message.content
                        break
                    sleep(5)
                
                await text_channel.set_permissions(players[W], read_messages=True, send_messages=False)
                    
                if answer == "":
                    answertext = "制限時間が経過したため、逆転はなしです。"
                else:
                    answertext = f"{players[W].display_name} さんの回答 **{answer}** が村人ワードと一致していれば、ウルフの逆転勝利です。"
            now = datetime.now().strftime('%Y/%m/%d %H:%M')
            endtexts = [
                    "今回のゲームで使用したワードは以下です。",
                    f"ジャンル **{junle}**",
                    f"村人ワード **{villager_word}**",
                    f"ウルフワード **{wolf_word}**",
                    (f"\n{answertext}\n" if loseWolf and inversion else "") + f"\n▲▲{now} ゲーム終了▲▲\n------------------------------------------------"  
            ]
            await text_channel.send("\n".join(endtexts))
            
        except Exception as e:
            print(e)
            now = datetime.now().strftime('%Y/%m/%d %H:%M')
            await text_channel.send(f"エラーが発生したためゲームを終了します。\n\n▲▲{now} ゲーム終了▲▲\n------------------------------------------------")
        finally:
            for i,member in enumerate(players):
                await vote_channels[i].delete()
                await text_channel.set_permissions(member, read_messages=True, send_messages=False)
                
                
            
    if command == "!dice":
        await message.channel.send(str(randint(1,6)))
	
    if command == "!test":
        await message.channel.send(str(randint(1,6)))
client.run(TOKEN)
        
    



"""
from discord.ext import commands
import os
import traceback

bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


bot.run(token)
"""
