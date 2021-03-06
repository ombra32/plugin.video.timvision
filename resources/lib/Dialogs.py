import xbmcgui

def get_text_input(label=""):
        dlg = xbmcgui.Dialog()
        return dlg.input(heading=label, type=xbmcgui.INPUT_ALPHANUM)

def get_password_input():
    dlg = xbmcgui.Dialog()
    return dlg.input(heading="Password", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)

def show_message(message, title='', level=xbmcgui.NOTIFICATION_ERROR):
    dialog = xbmcgui.Dialog()
    dialog.notification(heading=title, message=message, icon=level, time=3000)
    return True

def show_dialog(message,title=''):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading=title, line1=message)

def ask(message, title=''):
    return xbmcgui.Dialog().yesno(heading=title, line1=message)