const USER_API_URL = '/api/user';

const loginWindow = document.getElementById('login-window');
const loginUsernameIn = document.getElementById('login-username');
const loginPasswordIn = document.getElementById('login-password');
const loginSubmit = document.getElementById('login-submit');

const signupWindow = document.getElementById('signup-window');
const signupUsernameIn = document.getElementById('signup-username');
const signupEmailIn = document.getElementById('signup-email');
const signupPasswordIn = document.getElementById('signup-password');
const signupPasswordVerifyIn = document.getElementById('signup-password-verify');
const signupSubmit = document.getElementById('signup-submit');

const loggedinElements = document.getElementsByClassName('loggedin');
const loggedoutElements = document.getElementsByClassName('loggedout');
const logoutOpt = document.getElementById('logout-opt');

const credit = document.getElementById('credit');

const profileRowContainer = document.getElementById('profile-row-container')
const profileRowEmail = document.getElementById('profile-row-email');
const profileRowUsername = document.getElementById('profile-row-username');

class UserProfile {


}

class UserState {
  constructor () {
    logoutOpt.addEventListener('click', () => this.logout());
  }

  async setCurrentUser() {
    this.currentUser = await _get(USER_API_URL);
  }

  async refresh() {
    await this.setCurrentUser();
    this.setProfile();
    for (let element of loggedinElements) {
        (this.currentUser)? _show(element): _hide(element);
    }
    for (let element of loggedoutElements) {
        (this.currentUser)? _hide(element): _show(element);
    }
    if (this.currentUser) {
      credit.innerHTML = `welcome, ${this.currentUser.username}`;
    } else {
      credit.innerHTML = 'By Caspar Wylie';
    }
  }

  setProfile() {
    if (this.currentUser) {
      profileRowUsername.innerHTML = this.currentUser.username;
      profileRowEmail.innerHTML = this.currentUser.email;
    } else {
      profileRowUsername.innerHTML = '';
      profileRowEmail.innerHTML = '';
    }
  }

  async logout() {
    await _get(`${USER_API_URL}/logout`);
    Informer.inform('Logged out.', 'normal');
    this.refresh();
  }
}


class SignupForm {
  constructor() {
    signupSubmit.addEventListener('click', () => this.signupRequest());
  }

  async signupRequest() {
    if (
      signupUsernameIn.value &&
      signupEmailIn.value &&
      signupPasswordIn.value &&
      signupPasswordVerifyIn.value
    ) {
      if (signupPasswordVerifyIn.value != signupPasswordIn.value) {
        Informer.inform('Passwords do not match.', 'bad');
        return;
      }
      let response = await _post(`${USER_API_URL}/signup`, {
        'username': signupUsernameIn.value,
        'email': signupEmailIn.value,
        'password': signupPasswordIn.value
      });
      if (response.success) {
        this.successSignup();
      } else {
        this.failedSignup(response.errors);
      }
    } else {
      Informer.inform('All fields are required.', 'bad');
    }
  }

  successSignup() {
    Informer.inform('Successfully signed up! You can now login.', 'good');
    loginUsernameIn.value = signupUsernameIn.value;
    loginPasswordIn.value = signupPasswordIn.value;
    this.resetForm();
    _hide(signupWindow);
  }

  failedSignup(errors) {
    errors.forEach((error) => Informer.inform(error, 'bad'));
  }

  resetForm() {
    document.querySelectorAll('#signup-form input').forEach(
      (element) => element.value = ''
    )
  }
}


class LoginForm {
  constructor(userState) {
    this.userState = userState;
    loginSubmit.addEventListener('click', () => this.loginRequest());
  }

  async loginRequest() {
    if (loginUsernameIn.value && loginPasswordIn.value) {
      let response = await _post(`${USER_API_URL}/login`, {
        'username': loginUsernameIn.value,
        'password': loginPasswordIn.value
      });
      if (response.success) {
        await this.successLogin();
      } else {
        this.failedLogin(response.errors);
      }
    } else {
      Informer.inform('All fields are required.', 'bad');
    }
  }

  async successLogin() {
    Informer.inform('Successfully logged in!', 'good');
    await this.userState.refresh();
    this.resetForm();
    _hide(loginWindow);
  }

  failedLogin() {
    Informer.inform('Incorrect username or password.', 'bad');
  }

  resetForm() {
    document.querySelectorAll('#login-form input').forEach(
      (element) => element.value = ''
    )
  }
}

