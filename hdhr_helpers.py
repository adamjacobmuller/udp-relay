def get_vstatus_packed(libhdhr, device):
    vstatus = libhdhr.device_get_tuner_vstatus(device)
    return vstatus_pack(vstatus)


def vstatus_pack(vstatus):
    if vstatus[2].not_subscribed == 1:
        subscribed = 'f'
    else:
        subscribed = 't'

    if vstatus[2].not_available == 1:
        available = 'f'
    else:
        available = 't'

    if vstatus[2].copy_protected == 1:
        copy_protected = 't'
    else:
        copy_protected = 'f'

    return 'vchannel=%s:name=%s:auth=%s:cci=%s:cgms=%s:subscribed=%s:avaliable=%s:copy_protected=%s' % (
        vstatus[2].vchannel,
        vstatus[2].name,
        vstatus[2].auth,
        vstatus[2].cci,
        vstatus[2].cgms,
        subscribed,
        available,
        copy_protected
    )
