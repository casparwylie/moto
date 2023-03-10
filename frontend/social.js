const SOCIAL_API_URL = '/api/social';

const socialWindow = document.getElementById('social-window');
const viewCommentsOpt = document.getElementById('view-comments-opt');
const addCommentOpt = document.getElementById('add-comment-opt');
const commentIn = document.getElementById('add-comment-text');
const commentsContainer = document.getElementById('comments-container');
const commentsTitle = document.getElementById('comments-title');

class Social {
  constructor() {
    viewCommentsOpt.addEventListener('click', () => this.loadComments());
    addCommentOpt.addEventListener('click', () => this.saveComment());
  }

  getRaceUniqueId() {
    return racingPage.race.raceUniqueId;
  }

  async loadComments() {
    _show(socialWindow);
    commentsContainer.replaceChildren();
    let raceUniqueId = this.getRaceUniqueId();
    let results = await _get(
      `${SOCIAL_API_URL}/comments?race_unique_id=${raceUniqueId}`
    );
    if (results.comments.length > 0) {
      results.comments.forEach((comment) => this.addCommentRow(comment));
    } else {
      commentsContainer.innerHTML = 'No comments yet.';
    }
  }

  addCommentRow(comment) {
    let commentContainer = _el('div', {className: 'comment-container'});
    let infoText = `- ${comment.username} | ${comment.created_at}`;

    let commentTextContainer = _el('div', {
      className: 'comment-text-container', innerHTML: comment.text
    });
    let commentInfoContainer = _el('div', {
      className: 'comment-info-container', innerHTML: infoText
    });
    if (
      userState.currentUser &&
      userState.currentUser.username == comment.username
    ) {
      let commentDeleteOpt = _el('div', {
        className: 'comment-delete-opt', innerHTML: '&#10005;'
      });
      commentDeleteOpt.addEventListener('click', () => this.deleteComment(comment.id));
      commentContainer.appendChild(commentDeleteOpt);
    }
    commentContainer.appendChild(commentTextContainer);
    commentContainer.appendChild(commentInfoContainer);

    if (comment.garage_relation_sentence.length > 0) {
      let garageInfoContainer = _el('div', {
        className: 'garage-info-container',
        innerHTML: `*${comment.garage_relation_sentence}`,
      });
      commentContainer.appendChild(garageInfoContainer);
    }

    commentsContainer.appendChild(commentContainer);
  }

  async deleteComment(comment_id) {
    let result = await _post(
      `${SOCIAL_API_URL}/delete-comment`, {comment_id: comment_id}
    );
    if (result.success) {
      Informer.inform('Successfully deleted comment.', 'good');
      this.loadComments();
    }
  }

  async saveComment() {
    let raceUniqueId = this.getRaceUniqueId();
    if (raceUniqueId && commentIn.value.trim()) {
      let result = await _post(`${SOCIAL_API_URL}/add-comment`, {
        race_unique_id: raceUniqueId,
        text: commentIn.value,
      });
      if (result.success) {
        Informer.inform('Successfully added comment!', 'good');
        commentIn.value = "";
        this.loadComments();
      } else if (result._status_code == 403){
        Informer.inform('You must have an account to comment.', 'bad');
      } else if (result.errors) {
        result.errors.forEach((error) => Informer.inform(error, 'bad'));
      }
    }
  }
}
