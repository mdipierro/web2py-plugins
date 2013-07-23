def index():
    redirect('user')

def user():
    return dict(form=rpxauth())
