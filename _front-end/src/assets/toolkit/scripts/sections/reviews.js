import wanakana from '../vendor/wanakana.min';
import { revealToggle } from '../components/revealToggle';
import kwlog from '../util/kwlog';
import '../util/serializeObject';
import modals from '../vendor/modals';
modals.init({
  backspaceClose: false,
  callbackOpen: synonymModal,
  callbackClose: enableShortcuts,
});


// would really like to do a massive refactor, break out some functions as importable helpers
// undecided how I want to reorganise but it's becoming a spiderweb
// might use react just for reviews - since the template is only used to load in the review object
// instead we could load the page with a <div id="reactReview"></div> and ajax in the data
// and have much better organisation / handling of state

const $homeLink = $('.homelink');
const $reviewsLeft = $('#reviewsLeft');
const $reviewsDone = $('#reviewsDone');
const $reviewsCorrect = $('#reviewsCorrect');
const $progressBar = $('.progress-bar > .value');
const $meaning = $('#meaning');
const $srsIndicator = $('.streak > .icon');
const $userAnswer = $('#userAnswer');
const $answerPanel = $('#answerpanel');
const $submitButton = $('#submitAnswer');
const $ignoreButton = $('#ignoreAnswer');
const $srsUp = $('#srsUp > .content');
const $srsDown = $('#srsDown > .content');
const $reveal = $('.reveal');
const $detailKana = $('#detailKana');
const $detailKanji = $('#detailKanji');
const $synonymButton = $('#addSynonym');
const $synonymForm = $('#synonymForm');

let KW;
let currentVocab;
let remainingVocab;
let startCount;
let answer;
let correctTotal = 0;
let answeredTotal = 0;
let autoAdvancing = false;
const answerCorrectness = [];

// http://www.rikai.com/library/kanjitables/kanji_codes.unicode.shtml
// not including *half-width katakana / roman letters* since they should be considered typos
const japRegex = /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3400-\u4dbf]/;
function onlyJapaneseChars(str) {
  return [...str].every(char => japRegex.test(char));
}

function onlyKanji(str) {
  return [...str].every(char => char.charCodeAt(0) >= 19968 && char.charCodeAt(0) < 40879);
}

// Grab CSRF token off of dummy form.
const CSRF = $('#csrf').val();

function init() {
  // if not on reviews page do nothing
  if (!/review/.test(window.location.pathname)) return;

  // set initial values
  KW = simpleStorage.get('KW');
  remainingVocab = window.sessionVocab;
  startCount = remainingVocab.length;

  $reviewsLeft.text(startCount - 1);
  currentVocab = remainingVocab.shift();
  updateKanaKanjiDetails();
  updateSrsIndicator(currentVocab.streak);

  // event listeners
  wanakana.bind(document.querySelector('#userAnswer'));
  wanakana.bind(document.querySelector('#newKana')); // new synonym form input
  wanakana.bind(document.querySelector('#newKanji')); // new synonym form input

  // rotate or record on 'submit' rather than submitting form and page refreshing
  $submitButton.click(enterPressed);
  $answerPanel.submit(enterPressed);
  $ignoreButton.click(ignoreAnswer);

  // DEBUG
  $userAnswer.keydown((event) => {
    kwlog('kp', event.which, String.fromCharCode(event.which));
  });

  $synonymButton.click(synonymModal);
  $synonymForm.submit(handleSynonymForm);

  // ask a question
  $meaning.html(currentVocab.meaning);
  $userAnswer.focus();

  $homeLink.click(earlyTermination);
}

function getSrsRankName(num) {
  return num > 8 ? 'burned' :
         num > 7 ? 'enlightened' :
         num > 6 ? 'master' :
         num > 4 ? 'guru' : 'apprentice';
}

function updateSrsIndicator(rankName) {
  // using .attr('class') to completely wipe prev classes on update
  $srsIndicator.attr('class', `icon i-${rankName}`);
  $srsIndicator.closest('.streak').attr('data-hint', `${rankName}`);
}

function srsRankChange({ correct = false } = {}) {
  const rank = { val: currentVocab.streak, name: getSrsRankName(currentVocab.streak) };
  const adjustedRank = currentVocab.streak + (correct ? 1 : -1);
  const prevWrong = currentVocab.previouslyWrong;
  const newRank = { val: adjustedRank, name: getSrsRankName(adjustedRank) };
  const rankUp = !prevWrong && newRank.val > rank.val && newRank.name !== rank.name;
  const rankDown = newRank.val < rank.val && newRank.name !== rank.name;

  kwlog('rank:', rank, 'newRank:', newRank, 'rankUp:', rankUp, 'rankDown:', rankDown, 'prevWrong;', prevWrong);

  if (rankUp) {
    $srsUp.attr('data-after', newRank.name).addClass(`is-animating -${newRank.name}`);
    updateSrsIndicator(newRank.name);
  }

  if (rankDown) {
    $srsDown.attr('data-after', newRank.name).addClass(`is-animating -${newRank.name}`);
    updateSrsIndicator(newRank.name);
  }
}

function updateKanaKanjiDetails() {
  $detailKana.find('.-kana').html(currentVocab.readings.map(reading => `${reading} </br>`));
  $detailKanji.find('.-kanji').html(currentVocab.characters.map(kanji => `${kanji} </br>`));
}

function earlyTermination(ev) {
  ev.preventDefault();
  if (answeredTotal === 0) {
    window.location = '/kw/';
  } else {
    postSummary('/kw/summary/', answerCorrectness);
  }
}

function postSummary(path, params) {
  const form = document.createElement('form');
  form.setAttribute('method', 'post');
  form.setAttribute('action', path);
  form.setAttribute('class', 'u-visuallyhidden');


  // TODO: this is crazytown, treating an array as an object - need to refactor
  for (let key in params) {
    if (params.hasOwnProperty(key)) {
      const hiddenField = document.createElement('input');
      hiddenField.setAttribute('type', 'hidden');
      hiddenField.setAttribute('name', key);
      hiddenField.setAttribute('value', params[key]);

      form.appendChild(hiddenField);
    }
  }

  // CSRF hackery.
  const CsrfField = document.createElement('input');
  CsrfField.setAttribute('name', 'csrfmiddlewaretoken');
  CsrfField.setAttribute('value', CSRF);
  form.appendChild(CsrfField);
  document.body.appendChild(form);
  form.submit();
}

function endsWith(str, suffix) {
  return str.indexOf(suffix, str.length - suffix.length) !== -1;
}

function startsWith(str, prefix) {
  return str.slice(0, prefix.length) === prefix;
}

// Fixing the terminal n.
function addTerminalN(str) {
  if (endsWith(str, 'n')) answer = `${str.slice(0, -1)}ん`;
}

// Add tilde to ime input
function addStartingTilde(str) {
  const tildeJA = '〜';
  const tildeEN = '~';
  if (startsWith(str, tildeEN)) answer = tildeJA + str.slice(1);
  if (!startsWith(str, tildeJA)) answer = tildeJA + str;
}

function isEmptyString(str) {
  return str === '';
}

function compareAnswer() {
  kwlog('compareAnswer called');
  answer = $userAnswer.val().trim();

  if (isEmptyString(answer)) return;

  kwlog('Comparing', answer, 'with vocab item:');
  if (!!window.KWDEBUG) console.table(currentVocab);

  addTerminalN(answer);

  if (onlyJapaneseChars(answer)) {
    // user used japanese IME, proceed
    if (currentVocab.characters[0].startsWith('〜') && onlyKanji(answer)) addStartingTilde(answer);
  } else if (!wanakana.isHiragana(answer)) {
    // user used english that couldn't convert to full hiragana - don't proceed
    return nonHiraganaAnswer();
  }

  const inReadings = () => $.inArray(answer, currentVocab.readings) !== -1;
  const inCharacters = () => $.inArray(answer, currentVocab.characters) !== -1;
  const getMatchedReading = (hiraganaStr) => currentVocab.characters[currentVocab.readings.indexOf(hiraganaStr)];

  if (inReadings() || inCharacters()) {
    let advanceDelay = 800;

    markRight();
    processAnswer({ correct: true });

    // Fills the correct kanji into the input field based on the user's answers
    if (wanakana.isHiragana(answer)) $userAnswer.val(getMatchedReading(answer));

    if (KW.settings.showCorrectOnSuccess) {
      revealAnswers();
      if (KW.settings.autoAdvanceCorrect) advanceDelay = 1400;
    }

    if (KW.settings.autoAdvanceCorrect) {
      autoAdvancing = true;
      setTimeout(() => {
        // user advancing early by themselves sets autoAdvancing to false;
        if (autoAdvancing) enterPressed(null);
      }, advanceDelay);
    }
  } else {
    markWrong();
    // don't processAnswer() here
    // wait for submission or ignore answer - which is handled by event listeners for submit/enter
    if (KW.settings.showCorrectOnFail) revealAnswers();
  }

  enableButtons();
}

function synonymModal() {
  kwlog('synonymModal called');
  disableShortcuts();

  const $form = $('#synonymForm');
  const $answerField = $(wanakana.isHiragana(answer) ? '#newKana' : '#newKanji');
  const $notAnswerField = $('.input').not($answerField);

  // prepopulate
  $form.find('.wrappinglabel').each((i, el) => {
    const $el = $(el);
    $el.find('.input').val('');
    $el.find('.jisho').removeClass('-ghost');
  });

  $answerField.val(answer).next('.jisho').addClass('-ghost');
  $notAnswerField.next('.jisho').attr({ href: `http://jisho.org/search/${answer}` });

  setTimeout(() => $notAnswerField.focus(), 200);
}

function handleSynonymForm(ev) {
  kwlog('handleSynonymForm called');
  ev.preventDefault();
  const $this = $(this);
  const vocabID = currentVocab.user_specific_id;
  const $submitButton = $this.find('#synonymSubmit');
  const $validation = $this.find('.validation');
  const data = $this.serializeObject();

  if (Object.keys(data).every(key => data[key] !== '' && onlyJapaneseChars(data[key]))) {
    $validation.addClass('-hidden');
    addSynonym(vocabID, data);
    $submitButton.html('<span class="icon -loading"></span>');
    setTimeout(() => {
      ignoreAnswer({ animate: false });
      modals.closeModals();
      $submitButton.html('Submit');
    }, 750);
  } else {
    $validation.removeClass('-hidden');
  }
}

function addSynonym(vocabID, { kana, kanji } = {}) {
  // add for when in-memory item is returned to review queue
  currentVocab.readings.push(kana);
  currentVocab.characters.push(kanji);

  // save on server
  $.post('/kw/synonym/add', {
    csrfmiddlewaretoken: CSRF,
    user_specific_id: vocabID,
    kana,
    kanji,
  })
  .always(res => {
    kwlog(res);
  });
}

function processAnswer({ correct = false } = {}) {
  kwlog('processAnswer called');

  const currentvocabID = currentVocab.user_specific_id;

  if (correct === true) {
    // Ensures this is the first time the vocab has been answered in this session,
    // so it goes in the right container(incorrect/correct)

    // TODO: this is crazytown, treating an array as an object - need to refactor as obj
    if ($.inArray(currentvocabID, Object.keys(answerCorrectness)) === -1) {
      answerCorrectness[currentvocabID] = 1;
      currentVocab.previouslyWrong = false;
    } else {
      currentVocab.previouslyWrong = true;
    }
    correctTotal += 1;
    updateProgressBar(correctTotal / startCount * 100);
    srsRankChange({ correct: true });
  } else if (correct === false) {
    answerCorrectness[currentvocabID] = -1;
    currentVocab.previouslyWrong = true;
    remainingVocab.push(currentVocab);
    srsRankChange({ correct: false });
  }

  answeredTotal += 1;
  recordAnswer(currentvocabID, correct, currentVocab.previouslyWrong); // record on server
}

function recordAnswer(vocabID, correctness, previouslyWrong) {
  $.post('/kw/record_answer/', {
    csrfmiddlewaretoken: CSRF,
    user_specific_id: vocabID,
    user_correct: correctness,
    wrong_before: previouslyWrong,
  })
  .always(res => {
    kwlog(res);
  });
}

function ignoreAnswer({ animate = true } = {}) {
  kwlog('ignoreAnswer called');
  if (animate) {
    $userAnswer.addClass('shake');
    setTimeout(() => rotateVocab({ ignored: true }), 600);
  } else {
    rotateVocab({ ignored: true });
  }
}

function clearColors() {
  $userAnswer.removeClass('-marked -correct -incorrect -invalid');
}

function nonHiraganaAnswer() {
  clearColors();
  $userAnswer.addClass('-invalid');
}

function enableShortcuts() {
  $(document).on('keydown.KWshortcuts', handleShortcuts);
}

function disableShortcuts() {
  $(document).off('keydown.KWshortcuts', handleShortcuts);
}

function markWrong() {
  enableShortcuts();
  clearColors();
  $userAnswer.addClass('-marked -incorrect').prop({ disabled: true });
  $srsIndicator.addClass('-marked');
  $ignoreButton.removeClass('-hidden');
  $synonymButton.removeClass('-hidden');
}

function markRight() {
  enableShortcuts();
  clearColors();
  $userAnswer.addClass('-marked -correct').prop({ disabled: true });
  $srsIndicator.addClass('-marked');
}

function updateProgressBar(percent) {
  $progressBar.css({ width: `${percent}%` });
}

function resetQuizUI() {
  clearColors();
  disableButtons();
  disableShortcuts();
  updateKanaKanjiDetails();
  updateSrsIndicator(currentVocab.streak);
  $srsUp.removeClass('is-animating');
  $srsDown.removeClass('is-animating');
  $userAnswer.removeClass('shake');
  $userAnswer.val('').prop({ disabled: false }).focus();
}

function disableButtons() {
  $reveal.addClass('-hidden');
  $ignoreButton.addClass('-hidden');
  $detailKanji.find('.button').addClass('-disabled');
  $detailKana.find('.button').addClass('-disabled');
  $synonymButton.addClass('-hidden');
}

function enableButtons() {
  $detailKanji.find('.button').removeClass('-disabled');
  $detailKana.find('.button').removeClass('-disabled');
}

function revealAnswers({ kana, kanji } = {}) {
  if (!!kana) revealToggle($detailKana.find('.button'));
  else if (!!kanji) revealToggle($detailKanji.find('.button'));
  else {
    revealToggle($detailKana.find('.button'));
    revealToggle($detailKanji.find('.button'));
  }
}

function rotateVocab({ ignored = false, correct = false } = {}) {
  kwlog('rotateVocab called');

  if (!!ignored) {
    // put ignored answer back onto end of review queue
    remainingVocab.push(currentVocab);
  }

  if (remainingVocab.length === 0) {
    // kwlog('Summary post data', answerCorrectness);
    return postSummary('/kw/summary/', answerCorrectness);
  }

  currentVocab = remainingVocab.shift();

  if (!!correct) {
    $reviewsLeft.html(remainingVocab.length);
    $reviewsDone.html(correctTotal);
  }

  // guard against 0 / 0 (when first answer ignored)
  const percentCorrect = Math.floor((correctTotal / answeredTotal) * 100) || 0;

  kwlog(`
    remainingVocab.length: ${remainingVocab.length},
    currentVocab: ${currentVocab.meaning},
    correctTotal: ${correctTotal},
    answeredTotal: ${answeredTotal},
    percentCorrect: ${percentCorrect}`
  );

  $reviewsCorrect.html(percentCorrect);
  $meaning.html(currentVocab.meaning);

  resetQuizUI();
}

function enterPressed(event) {
  kwlog('eP:', event, 'autoAdvancing:', autoAdvancing);

  if (event != null) {
    event.stopPropagation();
    event.preventDefault();
  }

  autoAdvancing = false;

  if ($userAnswer.hasClass('-marked')) {
    if ($userAnswer.hasClass('-correct')) {
      rotateVocab({ correct: true });
    } else if ($userAnswer.hasClass('-incorrect')) {
      processAnswer({ correct: false });
      rotateVocab({ correct: false });
    }
  } else {
    compareAnswer();
  }
}

function handleShortcuts(ev) {
  if (ev.which === 13) {
    kwlog('handleShortcuts: not -marked, 13;');
    ev.stopPropagation();
    ev.preventDefault();
    enterPressed(null);
  } else if ($userAnswer.hasClass('-marked')) {
    kwlog('handleShortcuts: -marked, not 13;');
    ev.stopPropagation();
    ev.preventDefault();

    switch (true) {
      // Pressing P toggles phonetic reading
      case (ev.which === 80 || ev.which === 112):
        kwlog('case: P', 'event was:', ev);
        revealAnswers({ kana: true });
        break;

      // Pressing K toggles the actual kanji reading.
      case (ev.which === 75 || ev.which === 107):
        kwlog('case: K', 'event was:', ev);
        revealAnswers({ kanji: true });
        break;

      // Pressing F toggles both item info boxes.
      case (ev.which === 70 || ev.which === 102):
        kwlog('case: F', 'event was:', ev);
        revealAnswers();
        break;

      // Pressing S toggles both add synonym modal.
      case (ev.which === 83 || ev.which === 115):
        kwlog('case: S', 'event was:', ev);
        modals.openModal(null, '#newSynonym', {
          backspaceClose: false,
          callbackOpen: synonymModal,
          callbackClose: enableShortcuts,
        });
        break;

      // Pressing I ignores answer when input has been marked incorrect
      case (ev.which === 73 || ev.which === 105 || ev.which === 8):
        kwlog('case: I', 'event was:', ev);
        if ($userAnswer.hasClass('-incorrect')) ignoreAnswer();
        break;

      default:
        kwlog('switch through to default');
    }
  }
}

const api = {
  init,
};

export default api;
