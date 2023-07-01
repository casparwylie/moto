const USER_API_URL = '/api/user';

const loginWindow = document.getElementById('login-window');
const loginUsernameIn = document.getElementById('login-username');
const loginPasswordIn = document.getElementById('login-password');
const loginSubmit = document.getElementById('login-submit');
const forgotPasswordOpt = document.getElementById('forgot-password-opt');

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

const myProfileWindow = document.getElementById('myprofile-window');
const profileRowContainer = document.getElementById('profile-row-container')
const profileRowEmail = document.getElementById('profile-row-email');
const profileRowUsername = document.getElementById('profile-row-username');

const garageListingContainer = document.getElementById('profile-garage-container');
const addGarageToggle = document.getElementById('add-garage-toggle-opt');
const addGarageItemContainer = document.getElementById('add-garage-item-container');
const addGarageRecommendationsContainer = document.getElementById('racer-recommender');
const addGarageMakeIn = document.getElementById('add-garage-item-make');
const addGarageModelIn = document.getElementById('add-garage-item-model');
const addGarageYearIn = document.getElementById('add-garage-item-year');
const addGarageRelationIn = document.getElementById('add-garage-item-relation');
const addGarageSubmit = document.getElementById('add-garage-item-submit');

const profileDataViews = document.getElementsByClassName('profile-data-view');
const editProfileToggle = document.getElementById('edit-profile-toggle');
const editProfileContainer = document.getElementById('profile-edit-container');
const editUsernameSubmit = document.getElementById('edit-username-submit');
const editEmailSubmit = document.getElementById('edit-email-submit');
const editUsernameIn = document.getElementById('profile-edit-username');
const editEmailIn = document.getElementById('profile-edit-email');

const changePasswordToggle = document.getElementById('change-password-toggle');
const changePassContainer = document.getElementById('profile-change-pass-container');
const changePasswordSubmit = document.getElementById('change-password-submit');
const changePasswordOldIn = document.getElementById('profile-change-pass-old');
const changePasswordNewIn = document.getElementById('profile-change-pass-new');
const changePasswordNewVerifyIn = document.getElementById('profile-change-pass-verify-new');

const myRecentRacesContainer = document.getElementById('my-recent-races-container');

const GARAGE_ITEM_RELATIONSHIP_MAP = {
  'OWNS': 'Currently Own',
  'HAS_OWNED': 'Used To Own',
  'HAS_RIDDEN': 'Have Ridden',
  'SAT_ON': 'Once Sat On',
}
const EMPTY_GARAGE_TEXT = `
  Your garage is empty.
  Add bikes now (via + above) so others can see what you ride.
`

class MyRecentRacesInsight extends RaceListing {
  api_url = `${INSIGHTS_API_URL}/recent-races`;
  container = myRecentRacesContainer;
  window_ = myProfileWindow;
}

class Garage {
  constructor(userState) {
    addGarageToggle.addEventListener('click', () => this.toggleGarageAdding());
    addGarageSubmit.addEventListener('click', () => this.addItem());
    let recommender = new RacerRecommender(
      addGarageMakeIn,
      addGarageModelIn,
      addGarageYearIn,
      addGarageRecommendationsContainer,
    );
    recommender.assignTrigger(addGarageModelIn);
    this.userState = userState;
  }

  toggleGarageAdding() {
    (
      isShowing(addGarageItemContainer)
    )? _hide(addGarageItemContainer): _show(addGarageItemContainer);
  }

  async set() {
    let response = await _get(
      `${USER_API_URL}/garage?user_id=${this.userState.currentUser.user_id}`
    );
    garageListingContainer.replaceChildren();
    if (response.items.length == 0) {
      garageListingContainer.innerHTML = EMPTY_GARAGE_TEXT;
      return;
    }
    response.items.forEach((item) => this.setRow(item));
  }

  setRow(item) {
      let name = `
        ${item.make_name} ${item.name} ${item.year} -
        ${GARAGE_ITEM_RELATIONSHIP_MAP[item.relation]}
      `;
      let row = _el('div', {className: 'garage-item-row', innerHTML: name});
      let deleteOpt = _el('span', {
        className: 'garage-item-delete-opt', innerHTML: '&#10005;'
      });
      deleteOpt.addEventListener('click', () => this.deleteItem(item.model_id));
      row.appendChild(deleteOpt);
      garageListingContainer.appendChild(row);
  }

  async deleteItem(model_id) {
    let response = await _post(`${USER_API_URL}/garage/delete`, {
        model_id: model_id,
      }
    )
    if (response.success) {
        Informer.inform('Successfully deleted!', 'good');
    } else {
      Informer.inform('Unknown error.', 'bad');
    }
    this.set();
  }


  async addItem() {
    if (
      addGarageRelationIn.value
      && addGarageModelIn.value
      && addGarageMakeIn.value
    ) {
      let response = await _post(`${USER_API_URL}/garage`, {
          relation: addGarageRelationIn.value,
          name: addGarageModelIn.value,
          make_name: addGarageMakeIn.value,
          year: addGarageYearIn.value
        },
      );
      if (response.success) {
        Informer.inform('Successfully added!', 'good');
        addGarageMakeIn.value = '';
        addGarageModelIn.value = '';
        addGarageYearIn.value = '';
        this.set();
      } else {
        Informer.inform('Unknown error.', 'bad');
      }
      this.toggleGarageAdding();
    } else {
      Informer.inform('All fields required.', 'bad');
    }
  }
}


class Profile {

  constructor(userState) {
    editProfileToggle.addEventListener(
      'click', () => this.toggleEditProfileData()
    );
    changePasswordToggle.addEventListener(
      'click', () => this.toggleEditChangePassword()
    );
    changePasswordSubmit.addEventListener(
      'click', () => this.changePassword()
    );
    editEmailSubmit.addEventListener(
      'click', () => this.editUserField('email', editEmailIn)
    );
    editUsernameSubmit.addEventListener(
      'click', () => this.editUserField('username', editUsernameIn)
    );
    this.userState = userState;
    this.garage = new Garage(userState);
  }

  async setAll() {
    this.setProfileData();
    this.setRecentRaces();
    await this.garage.set();
  }

  setProfileData() {
    profileRowUsername.innerHTML = this.userState.currentUser.username;
    profileRowEmail.innerHTML = this.userState.currentUser.email;
  }

  unsetAll() {
    profileRowUsername.innerHTML = '';
    profileRowEmail.innerHTML = '';
    resetForm('profile-change-pass-container');
    resetForm('profile-edit-container');
  }

  resetProfileDataView() {
    for (let view of profileDataViews) _hide(view);
  }


  async setRecentRaces() {
    let user_id = this.userState.currentUser.user_id;
    let listing = new MyRecentRacesInsight();
    listing.api_url += `?user_id=${user_id}`;
    listing.populate();
  }

  toggleEditProfileData() {
    if (isShowing(editProfileContainer))  {
      this.resetProfileDataView();
      _show(profileRowContainer);
    }  else {
      this.resetProfileDataView();
      _show(editProfileContainer);
    }
  }

  toggleEditChangePassword() {
    if (isShowing(changePassContainer))  {
      this.resetProfileDataView();
      _show(profileRowContainer);
    }  else {
      this.resetProfileDataView();
      _show(changePassContainer);
    }
  }

  async changePassword() {
    if (
      changePasswordOldIn.value &&
      changePasswordNewIn.value &&
      changePasswordNewVerifyIn.value
    ) {
      if (changePasswordNewIn.value != changePasswordNewVerifyIn.value) {
        Informer.inform('Passwords do not match.', 'bad');
        return;
      }
      let response = await _post(`${USER_API_URL}/change-password`, {
        'old': changePasswordOldIn.value,
        'new': changePasswordNewIn.value,
      });
      if (response.success) {
        Informer.inform('Successfully changed!', 'good');
        resetForm('profile-change-pass-container');
        this.toggleEditChangePassword();
      } else {
        response.errors.forEach((error) => Informer.inform(error, 'bad'));
      }
    } else {
      Informer.inform('All fields are required.', 'bad');
    }
  }

  unsetChangePassword() {
    changePasswordOldIn.value = '';
    changePasswordNewIn.value = ''
    changePasswordNewVerifyIn.value = '';
  }

  async editUserField(fieldName, inputElement) {
    if (inputElement.value) {
      let response = await _post(`${USER_API_URL}/edit`, {
        field: fieldName,
        value: inputElement.value,
      })
      if (response.success) {
        Informer.inform('Successfully updated!', 'good');
        this.userState.refresh();
        this.toggleEditProfileData();
        resetForm('profile-edit-container');
      } else {
        response.errors.forEach((error) => Informer.inform(error, 'bad'));
      }
    }
  }
}


class UserState {
  constructor () {
    logoutOpt.addEventListener('click', () => this.logout());
    this.profile = new Profile(this);
    this.currentUser = null;
  }

  async refresh() {
    if (getCookie('session_token')) {
      for (let element of loggedinElements) _show(element);
      for (let element of loggedoutElements) _hide(element);
      let response = await _get(USER_API_URL);
      if (response._status_code == 200) {
        this.currentUser = response
        await this.loadUser();
        return
      }
    }
    for (let element of loggedinElements) _hide(element);
    for (let element of loggedoutElements) _show(element);
    this.unloadUser();
  }

  async loadUser() {
    credit.innerHTML = `welcome, ${this.currentUser.username}`;
    await this.profile.setAll();
  }

  unloadUser() {
    credit.innerHTML = 'Enter the make and models of the motorcycles you want to race...';
    this.profile.unsetAll();
  }

  async logout() {
    await _get(`${USER_API_URL}/logout`);
    Informer.inform('Logged out.', 'good');
    this.refresh();
  }
}


class SignupForm {
  constructor() {
    signupSubmit.addEventListener('click', () => this.signupRequest());
    signupPasswordVerifyIn.addEventListener('keypress', (evt) => this.enterTrigger(evt));
  }

  enterTrigger(evt) {
    if (evt.key === "Enter") {
      event.preventDefault();
      signupSubmit.click();
    }
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
      _hide(signupSubmit);
      renderHeaderLoading('signup-header-image');
      let response = await _post(`${USER_API_URL}/signup`, {
        username: signupUsernameIn.value,
        email: signupEmailIn.value,
        password: signupPasswordIn.value
      });
      _show(signupSubmit);
      unrenderHeaderLoading('signup-header-image');
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
    resetForm('signup-form');
    _hide(signupWindow);
  }

  failedSignup(errors) {
    errors.forEach((error) => Informer.inform(error, 'bad'));
  }
}


class LoginForm {
  constructor(userState) {
    this.userState = userState;
    loginSubmit.addEventListener('click', () => this.loginRequest());
    forgotPasswordOpt.addEventListener('click', () => this.toggleForgotPassword());
    loginPasswordIn.addEventListener('keypress', (evt) => this.enterTrigger(evt));
    this.forgotPasswordMode = false;
  }

  enterTrigger(evt) {
    if (evt.key === "Enter") {
      event.preventDefault();
      loginSubmit.click();
    }
  }

  toggleForgotPassword() {
    if (!this.forgotPasswordMode) {
      loginUsernameIn.placeholder = 'Email...';
      loginSubmit.innerHTML = 'Send me a link';
      forgotPasswordOpt.innerHTML = 'Back to login';
      _hide(loginPasswordIn);
      this.forgotPasswordMode = true;
    } else {
      loginUsernameIn.placeholder = 'Username...';
      loginSubmit.innerHTML = 'Login';
      forgotPasswordOpt.innerHTML = 'Forgot Password?';
      _show(loginPasswordIn);
      this.forgotPasswordMode = false;
    }
  }

  async forgotPasswordRequest() {
    if (loginUsernameIn.value.trim()) {
      let result = await _post(
        `${USER_API_URL}/forgot-password`,
        {email: loginUsernameIn.value},
      );
      if (result.success) {
        Informer.inform('You have been sent an email to reset your password.', 'good');
        loginUsernameIn.value = '';
      } else {
        result.errors.forEach((error) => Informer.inform(error, 'bad'));
      }
    }
  }

  async loginRequest() {
    if (this.forgotPasswordMode) {
      await this.forgotPasswordRequest();
      return;
    }
    if (loginUsernameIn.value.trim() && loginPasswordIn.value.trim()) {
      let response = await _post(`${USER_API_URL}/login`, {
        username: loginUsernameIn.value,
        password: loginPasswordIn.value
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
    resetForm('login-form');
    _hide(loginWindow);
  }

  failedLogin() {
    Informer.inform('Incorrect username or password.', 'bad');
  }
}
