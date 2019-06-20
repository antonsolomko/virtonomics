@property
def messages(self):
    url = self.domain_ext + 'common/util/setpaging/usermain/messageIncomingList/400'
    self.session.get(url)
    url = self.domain_ext + 'user/privat/persondata/message/system?old'
    page = self.session.tree(url)
    xp = '//tr[@id="newmesg"]'
    result = {}
    for row in page.xpath(xp):
        message_id = int(row.xpath('./td/input/@value')[0])
        title = str(row.xpath('./td[last()]/a/text()')[0])
        result[message_id] = title
    return result


def mark_messages_as(self, messages, mark_as='Read'):
    """Mark messages as read (by default) or unread.
    
    Arguments:
        messages (iterable): List of messages ids.
        mark_as (str): 'Read' or 'Unread'.
    
    Returns:
        POST request responce.
    """
    
    url = self.domain_ext + 'user/privat/persondata/message/system'
    if mark_as not in ('Read', 'Unread'):
        return
    data = {
        'markas': mark_as,
        'message[]': list(messages)
        }
    self.session.post(url, data=data)