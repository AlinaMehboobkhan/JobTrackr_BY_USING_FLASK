# forms.py (or you can place this in app.py)
class RegisterForm:
    def __init__(self, username='', email='', password='', confirm_password=''):
        self.username = username
        self.email = email
        self.password = password
        self.confirm_password = confirm_password
        self.errors = {}

    def validate(self):
        if not self.username or len(self.username) < 3 or len(self.username) > 25:
            self.errors['username'] = 'Username must be between 3 and 25 characters.'
        if not self.email or '@' not in self.email:
            self.errors['email'] = 'Invalid email address.'
        if not self.password or len(self.password) < 6:
            self.errors['password'] = 'Password must be at least 6 characters.'
        if self.password != self.confirm_password:
            self.errors['confirm_password'] = 'Passwords do not match.'
        return not self.errors

class LoginForm:
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password
        self.errors = {}

    def validate(self):
        if not self.username:
            self.errors['username'] = 'Username is required.'
        if not self.password:
            self.errors['password'] = 'Password is required.'
        return not self.errors

# Add similar classes for JobForm, AvailableJobForm, and EditProfileForm


class JobForm:
    def __init__(self, job_title='', company='', status='', applied_date='', follow_up_date=None):
        self.job_title = job_title
        self.company = company
        self.status = status
        self.applied_date = applied_date
        self.follow_up_date = follow_up_date
        self.errors = {}

    def validate(self):
        if not self.job_title:
            self.errors['job_title'] = 'Job title is required.'
        if not self.company:
            self.errors['company'] = 'Company name is required.'
        if not self.status:
            self.errors['status'] = 'Status is required.'
        if not self.applied_date:
            self.errors['applied_date'] = 'Applied date is required.'
        return not self.errors

class AvailableJobForm:
    def __init__(self, job_title='', company='', posted_date=''):
        self.job_title = job_title
        self.company = company
        self.posted_date = posted_date
        self.errors = {}

    def validate(self):
        if not self.job_title:
            self.errors['job_title'] = 'Job title is required.'
        if not self.company:
            self.errors['company'] = 'Company name is required.'
        if not self.posted_date:
            self.errors['posted_date'] = 'Posted date is required.'
        return not self.errors

class EditProfileForm:
    def __init__(self, username='', email=''):
        self.username = username
        self.email = email
        self.errors = {}

    def validate(self):
        if not self.username or len(self.username) < 3 or len(self.username) > 25:
            self.errors['username'] = 'Username must be between 3 and 25 characters.'
        if not self.email or '@' not in self.email:
            self.errors['email'] = 'Invalid email address.'
        return not self.errors
