from contact_form.forms import ContactForm


class UserContactCustomForm(ContactForm):

    # Jam the originating User into the recipient list so we can reply-all to them.
    def recipient_list(self):
        recipients = [mail_tuple[1] for mail_tuple in settings.MANAGERS]
        recipients.append(self.cleaned_data['email'])
        return recipients
