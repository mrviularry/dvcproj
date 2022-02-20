import pickle
import logging
from random import randint
from twilio.rest import Client
from telegram.ext import (
    Updater,
    CommandHandler, 
    MessageHandler, 
    ConversationHandler,
    Filters, 
    CallbackQueryHandler, 
    CallbackContext
)
from telegram import  (
    Update,
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    KeyboardButton, 
    ReplyKeyboardMarkup, 
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

# Save each users OTP Request in dict form {UserID:OTP}
OnGoingVerification = {} 

# Your Account SID from twilio.com/console
account_sid = "AC66f5bbdf200a40b03c6235f489fae542"
# Your Auth Token from twilio.com/console
auth_token  = "81f5b3be09443ff1d33248cb33f1871c"

client = Client(account_sid, auth_token)

# Members DB ---------------------------------------
membersList = []
with open('MembersDB.data','rb') as membersDatabase:
    membersList = pickle.load(membersDatabase)
#---------------------------------------------------
withdrawl_done = 500
#---------------------------------------------------
def modify_markdown_string(inputstring):
    outputstring = inputstring
    char = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in char:
        outputstring = outputstring.replace(char, f'\\{char}')
    return outputstring

def refNotify(NAME, CID, Level, Reward):
    return f"🎉 Congratulations, {NAME} "+f"[➶](tg://user?id={CID})"+f" joined your Level {Level} network\.\nReward : {Reward}% of Total Purchase Amount"

WALLET, WITHDRAW = 0, 1

def cancel(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    update.message.reply_text(
        '✅ Operation Cancelled'
    )
    return ConversationHandler.END

def setWalletButtonResponder(update: Update, _:CallbackContext) -> int:
    _.bot.send_message(chat_id=update.callback_query.from_user.id, text="Ok, Now send your Paytm Number like `\+919876543210` or you must cancel this operation with /cancel command if you are not setting your wallet", parse_mode='MarkdownV2')    
    return WALLET

def wallet(update: Update, _:CallbackContext) -> int:
    global membersList

    for member in membersList:
        if member['TgID'] == update.message.chat.id:
            member['PaytmWallet'] = update.message.text

            with open('MembersDB.data', 'wb') as membersDatabase:
                pickle.dump(membersList, membersDatabase)
            _.bot.send_message(chat_id=update.message.chat.id, text='Wallet Updated Successfully')
            break
    return ConversationHandler.END

def withdrawButtonResponder(update: Update, _:CallbackContext) -> int:
    _.bot.send_message(chat_id=update.message.chat.id, text="Send Amount you want to withdraw or send /cancel to cancle this operation")
    return WITHDRAW

def withdraw(update: Update, _:CallbackContext) -> int:
    amount = update.message.text
    check = True

    if len(amount.split('.',1)) <= 2:
        for each in amount.split('.',1):
            if not each.isnumeric():
                check = False
                break

    if check:
        for member in membersList:
            if member['TgID'] == update.message.chat.id:
                if not member['PaytmWallet']:
                    update.message.reply_text('Please set wallet first')
                
                elif float(amount) == 0:
                    update.message.reply_text("Are you drunk? You can't withdraw Nil amount")

                elif float(amount) <= member['Balance']:
                    member['Balance'] -= float(amount)

                    with open('MembersDB.data', 'wb') as membersDatabase:
                        pickle.dump(membersList, membersDatabase)

                    update.message.reply_text('Withdrawl Requested Successfully')
                    _.bot.send_message(chat_id='@UREAG', text=f"🔋 New Withdrawl Requested\n\nUser : {modify_markdown_string(member['FirstName'])}\n\nRefers : {len(member['Childs'])}\n\nLink : [{member['TgID']}](tg://user?id={member['TgID']})\n\nAmount : {modify_markdown_string(amount)}\n\nPaytm Number : \+{member['PaytmWallet'][1:]}", parse_mode='MarkdownV2')
                
                else:
                    update.message.reply_text("You Don't have enough money")            
                break
    else:
        update.message.reply_text(text='✅ Operation Cancelled due to Invalid amount')
    
    return ConversationHandler.END

def main_menu(update: Update, _:CallbackContext) -> None:
    global membersList

    userData = None
    for member in membersList:
        if member['TgID'] == update.message.chat.id:
            userData = member

    if update.message.text == '💷 Balance':
        reply = f"🤴 User : [➶](tg://user?id={userData['TgID']}) {modify_markdown_string(userData['FirstName'])}\n\n💰 Balance : {modify_markdown_string(str(userData['Balance']))}₹\n\n🏧 Minimum Withdraw : 5₹💵"
        update.message.reply_text(reply, parse_mode='MarkdownV2')
    
    elif update.message.text == '👥 Referral':
        reply = f"🧑🏻‍✈️ Your Total Invites : {len(userData['Childs'])} Users\n\n 🎊 Per Referral 2Rs\n\n ❌ Fake refer no payment\n\n✅ Your Referal link : https://t\.me/Appy\_pybot?start\={userData['TgID']}"
        update.message.reply_text(reply, parse_mode='MarkdownV2')

    elif update.message.text == '📊 Statistics':
        reply = f"📊 Total Active Members : {len(membersList)} Users\n\n➕ Total successful Withdraw : {round(withdrawl_done)}₹"
        update.message.reply_text(reply)
    
    elif update.message.text == '💼 Set Wallet':
        update.message.reply_text(text=f"Wallet Settings ⚙️\n\n💼 Wallet : {userData['PaytmWallet']}\n\nClick on the below button to set or change your wallet", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='✏️ Set Wallet', callback_data='set.Wallet')]]))

    elif update.message.text == '🔰 Check Refers':
        if userData['Childs']:
            reply = f"Referral List \n"
            for child in userData['Childs']:
                reply += f"\n🧑🏻‍✈️ {userData['Childs'].index(child) + 1} [User](tg://user?id={child})"
            update.message.reply_text(reply, parse_mode='MarkdownV2')
        else:
            update.message.reply_text(text="❌ You didn't referred any friend")
    else:
        pass

def checkMembership(update: Update, _:CallbackContext) -> None:
    global membersList
    update.callback_query.answer()

    user = _.bot.get_chat_member(chat_id='@UREAG', user_id=update.callback_query.message.chat.id)
    referralBonus = 10

    if user.status == 'member':
        #----------Check If the Sender is present in DB or Not?----------#                    
        for member in membersList:
            if member['TgID'] == update.callback_query.message.chat.id:
                if not member['isParentRewarded']:
                    for parent in membersList:
                        if parent['TgID'] == member['ParentTgID']:
                            parent['Balance'] += referralBonus
                            _.bot.send_message(chat_id=parent['TgID'], text="New User Joined With Your Link", parse_mode='MarkdownV2')

                            member['isParentRewarded'] = True

                            with open('MembersDB.data', 'wb') as membersDB:
                                pickle.dump(membersList, membersDB)
                            break
                break

        KB = [
            [KeyboardButton(text='💷 Balance'), KeyboardButton(text='👥 Referral')],
            [KeyboardButton(text='📊 Statistics'), KeyboardButton(text='🏧 Withddraw')],
            [KeyboardButton(text='💼 Set Wallet'), KeyboardButton(text='🔰 Check Refers')]
        ]
        update.callback_query.message.reply_text(text='🔝 Main Menu', reply_markup=ReplyKeyboardMarkup(keyboard=KB, resize_keyboard=True))
        #----------------------------------------------------------------#

    else:
        update.callback_query.message.reply_text('❌ You must join our channel')
        
def verify(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()
    if len(data) == 2 and data[1].isdigit():
        global OnGoingVerification
        UID = update.effective_user.id
        OTP = int(data[1])

        if OnGoingVerification.get(UID) and OnGoingVerification[UID] == OTP:
            update.effective_message.reply_text("Mobile Verified")
        else:
            # Failure Message
            pass
    else:
        update.effective_message.reply_text("use format /verify <OTP>")

def setMobile(update: Update, _: CallbackContext):
    data = update.effective_message.text.split()
    if len(data) == 2 and data[1][0] == '+' and data[1][1:].isdigit():
        print ('A')
        global OnGoingVerification
        UID = update.effective_user.id
        OTP = randint(100001, 999999)
        mobile = data[1]
        OnGoingVerification[UID] = OTP
        message = client.messages.create(to=mobile, from_="+18333511115", body=f"OTP {OTP}")
        print (message)
        update.effective_message.reply_text(f"We Just Dropped a OTP to {mobile}, please verify it by sending /verify <OTP>")
    else:
        update.effective_message.reply_text("use format /setmobile +<MobileNumber>")

def start(update: Update, _: CallbackContext) -> None:
    global membersList
    
    update.message.reply_text(
        text="🎉 Join our Official Payment Channel to Start This Bot\n\n➡️ @UREAG\n\nAfter Join Channel Click Bellow Button", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='✅ Check', callback_data='checkMembership')]])
    )
    
    MSG = update.message.text
    CID = update.effective_chat.id
    NAME = update.effective_chat.first_name
    
    userData = None
    #----------Check If the Sender is present in DB or Not?----------#                    
    for member in membersList:
        if member['TgID'] == CID:
            userData = member
            break
    #----------------------------------------------------------------#
    #----------If sender is a new to bot then Update MembersDB----------#
    if not userData: #----------- New User Joined -----------------------
        newMemberTemplate = {
            'TgID': CID,
            'FirstName': NAME,
            'ParentTgID': None,
            'isParentRewarded' : False,
            'Balance': 0.0,
            'PaytmWallet': None,
            'Childs':[], #'TgID1', 'TgID2', 'TgID3', ...
        }

        if len(MSG) >= 8 and MSG[7:].isnumeric():
            for L1Invitee in membersList:
                if L1Invitee['TgID'] == int(MSG[7:]):
                    L1Invitee['Childs'] += [CID]
                    newMemberTemplate['ParentTgID'] = L1Invitee['TgID']
                    break

        membersList += [newMemberTemplate]

        with open('MembersDB.data','wb') as membersDatabase:
            pickle.dump(membersList, membersDatabase)
        
        # Notify Admin --------------------------------------------------------------------------------------------------------
        _.bot.send_message(chat_id=1667505517, text=f"[{CID}](tg://user?id={CID})"+" New Bot User", parse_mode='MarkdownV2')
        #----------------------------------------------------------------------------------------------------------------------
    
def main() -> None:
    updater = Updater(token="5168502719:AAG1W3L-OJXMGHXuaE-ZH4MGClWP7yOJIhE", use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(setWalletButtonResponder, pattern='set.')],
        states={WALLET: [MessageHandler(Filters.regex('^(\+1)\d{10}$'), wallet)]},
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    withdraw_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^(🏧 Withddraw)$'), withdrawButtonResponder)],
        states={WITHDRAW: [MessageHandler(Filters.text, withdraw)]},
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(CommandHandler('start', start, Filters.chat_type.private))
    dp.add_handler(CommandHandler('setMobile', setMobile, Filters.chat_type.private))
    dp.add_handler(conv_handler)
    dp.add_handler(withdraw_conv_handler)
    dp.add_handler(CallbackQueryHandler(checkMembership, pattern='^check'))
    dp.add_handler(MessageHandler(filters=Filters.chat_type.private & Filters.text & ~Filters.command, callback=main_menu))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
