import wanakana from '../vendor/wanakana.min';
import kwlog from '../util/kwlog';
import '../util/serializeObject';
import modals from '../vendor/modals';
modals.init({
  backspaceClose: false,
  callbackOpen: synonymModal,
  callbackClose: enableShortcuts,
});

// cachey cache
const $homeLink = $('.homelink');
const $reviewsLeft = $('#reviewsLeft');
const $reviewsDone = $('#reviewsDone');
const $reviewsCorrect = $('#reviewsCorrect');
const $progressBar = $('.progress-bar > .value');
const $meaning = $('#meaning');
const $srsIndicator = $('.streak > .icon');
const $userAnswer = $('#userAnswer');
const $answerPanel = $('#answerPanel');
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
let ignored = false;
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
  updateSrsIndicator(getSrsRankName(currentVocab.streak));

  // event listeners
  wanakana.bind(document.querySelector('#userAnswer'));
  wanakana.bind(document.querySelector('#newKana')); // new synonym form input
  wanakana.bind(document.querySelector('#newKanji')); // new synonym form input

  // rotate or record on 'submit' rather than submitting form and page refreshing
  $submitButton.click(enterPressed);
  $answerPanel.submit(enterPressed);
  $ignoreButton.click(ignoreIncorrectAnswer);
  $synonymButton.click(synonymModal);
  $synonymForm.submit(handleSynonymForm);

  // ask a question
  $meaning.html(currentVocab.meaning);
  $userAnswer.focus();

  $('.revealToggle').click(function revealButtonClick() {
    let $this = $(this);
    if (!$this.hasClass('-disabled')) revealToggle($this);
  });

  $homeLink.click(earlyTermination);

  // DEBUG
  if (!!window.KWDEBUG) {
    $userAnswer.keydown((event) => {
      kwlog('kp', event.which, String.fromCharCode(event.which));
    });
  }
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

  kwlog('--- srsRankChange---\n',
    'rank:', rank,
    '\nnewRank:', newRank,
    '\nrankUp:', rankUp,
    '\nrankDown:', rankDown,
    '\nprevWrong:', prevWrong
  );

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

  kwlog('Comparing', answer, `with vocab item ${currentVocab.user_specific_id}:`);
  if (!!window.KWDEBUG) console.group(currentVocab);

  addTerminalN(answer);

  if (onlyJapaneseChars(answer)) {
    // user used japanese IME, proceed
    if (currentVocab.characters[0].startsWith('〜') && onlyKanji(answer)) addStartingTilde(answer);
  } else if (!wanakana.isHiragana(answer)) {
    // user used english that couldn't convert to full hiragana - don't proceed
    nonHiraganaAnswer();
    return;
  }

  const inReadings = () => $.inArray(answer, currentVocab.readings) !== -1;
  const inCharacters = () => $.inArray(answer, currentVocab.characters) !== -1;
  const getMatchedReading = (hiraganaStr) => currentVocab.characters[currentVocab.readings.indexOf(hiraganaStr)];

  if (inReadings() || inCharacters()) {
    let advanceDelay = 800;

    markRight();

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
      ignoreIncorrectAnswer({ animate: false });
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

    // TODO: this is crazytown, treating an array as an object - should refactor as obj
    if ($.inArray(currentvocabID, Object.keys(answerCorrectness)) === -1) {
      answerCorrectness[currentvocabID] = 1;
      currentVocab.previouslyWrong = false;
    } else {
      currentVocab.previouslyWrong = true;
    }
    correctTotal += 1;
    updateProgressBar(correctTotal / startCount * 100);
  } else if (correct === false) {
    answerCorrectness[currentvocabID] = -1;
    currentVocab.previouslyWrong = true;
    remainingVocab.push(currentVocab);
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

function ignoreIncorrectAnswer({ animate = true } = {}) {
  kwlog('ignoreIncorrectAnswer called');

  if (ignored === false) {

    // using ignored flag to guard against multiple ignore submission spams before quiz ui has fully reset/rotated
    ignored = true;
    kwlog('ignoreIncorrectAnswer applied');
    remainingVocab.push(currentVocab);

    if (animate) {
      $userAnswer.addClass('shake');
      setTimeout(() => rotateVocab(), 600);
    } else {
      rotateVocab();
    }
  }
}

function ignoreCorrectAnswer({ animate = true } = {}) {
  kwlog('ignoreCorrectAnswer called');

  if (ignored === false) {

    // using ignored flag to guard against multiple ignore submission spams before quiz ui has fully reset/rotated
    ignored = true;
    kwlog('ignoreCorrectAnswer applied');
    processAnswer({ correct: false });

    if (animate) {
      $userAnswer.addClass('shake');
      setTimeout(() => rotateVocab(), 600);
    } else {
      rotateVocab();
    }
  }
}

function clearColors() {
  $answerPanel.removeClass('-marked -correct -incorrect -invalid');
}

function nonHiraganaAnswer() {
  clearColors();
  $answerPanel.addClass('-invalid');
}

function enableShortcuts() {
  document.addEventListener('keydown', handleShortcuts);
}

function disableShortcuts() {
  document.removeEventListener('keydown', handleShortcuts);
}

function markWrong() {
  enableShortcuts();
  clearColors();
  kwlog($answerPanel);
  $answerPanel.addClass('-marked -incorrect');
  $userAnswer.prop({ disabled: true });
  $userAnswer.blur();
  srsRankChange({ correct: false });
  $ignoreButton.removeClass('-hidden');
  $synonymButton.removeClass('-hidden');
}

function markRight() {
  enableShortcuts();
  clearColors();
  $answerPanel.addClass('-marked -correct');
  $userAnswer.prop({ disabled: true });
  $userAnswer.blur();
  srsRankChange({ correct: true });
}

function updateProgressBar(percent) {
  $progressBar.css({ width: `${percent}%` });
}

function resetQuizUI() {
  clearColors();
  disableButtons();
  disableShortcuts();
  updateKanaKanjiDetails();
  updateSrsIndicator(getSrsRankName(currentVocab.streak));
  $srsUp.attr('class', 'content icon i-plus');
  $srsDown.attr('class', 'content icon i-minus');
  $userAnswer.removeClass('shake');
  $userAnswer.val('').prop({ disabled: false }).focus();
  ignored = false;
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

function revealToggle($el) {
  $el.siblings('.revealTarget').toggleClass('-hidden');
}

function revealAnswers({ kana, kanji } = {}) {
  if (!!kana) revealToggle($detailKana.find('.button'));
  else if (!!kanji) revealToggle($detailKanji.find('.button'));
  else {
    revealToggle($detailKana.find('.button'));
    revealToggle($detailKanji.find('.button'));
  }
}

function rotateVocab({ correct = false } = {}) {
  kwlog('rotateVocab called');

  if (remainingVocab.length === 0) {
    // kwlog('Summary post data', answerCorrectness);
    postSummary('/kw/summary/', answerCorrectness);
    return;
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
  kwlog('enterPressed:', event, 'autoAdvancing:', autoAdvancing);

  if (event != null) {
    event.stopPropagation();
    event.preventDefault();
  }

  autoAdvancing = false;

  if ($answerPanel.hasClass('-marked')) {
    if ($answerPanel.hasClass('-correct')) {
      processAnswer({ correct: true });
      rotateVocab({ correct: true });
    } else if ($answerPanel.hasClass('-incorrect')) {
      processAnswer({ correct: false });
      rotateVocab({ correct: false });
    }
  } else {
    compareAnswer();
  }
}

function handleShortcuts(ev) {
  if (ev.which === 13) {
    kwlog('handleShortcuts called: not -marked, keycode:', ev.which);
    ev.preventDefault();
    ev.stopPropagation();
    enterPressed(null);
  } else if ($answerPanel.hasClass('-marked')) {
    kwlog('handleShortcuts called: -marked, keycode:', ev.which);

    switch (true) {
      // Pressing P toggles phonetic reading
      case (ev.which === 80 || ev.which === 112):
        kwlog('switch case: P');
        revealAnswers({ kana: true });
        break;

      // Pressing K toggles the actual kanji reading.
      case (ev.which === 75 || ev.which === 107):
        kwlog('switch case: K');
        revealAnswers({ kanji: true });
        break;

      // Pressing F toggles both item info boxes.
      case (ev.which === 70 || ev.which === 102):
        kwlog('switch case: F');
        revealAnswers();
        break;

      // Pressing S toggles add synonym modal.
      case (ev.which === 83 || ev.which === 115):
        kwlog('switch case: S');
        modals.openModal(null, '#newSynonym', {
          backspaceClose: false,
          callbackOpen: synonymModal,
          callbackClose: enableShortcuts,
        });
        break;

      // Pressing I ignores answer when input has been marked incorrect
      case (ev.which === 73 || ev.which === 105 || ev.which === 8 || ev.which === 191):
        ev.preventDefault();
        kwlog('case: I', 'event was:', ev);
        if ($answerPanel.hasClass('-incorrect')) ignoreIncorrectAnswer();
        break;

      // Secret hidden ninja ability to ignore CORRECT answer for user Meem0
      case (ev.which === 220):
        ev.preventDefault();
        kwlog('case: \\', 'event was:', ev);
        if ($answerPanel.hasClass('-correct')) {
          $answerPanel.addClass('-incorrect').removeClass('-correct');
          ignoreCorrectAnswer();
        }
        break;

      default:
        kwlog('handleShortcuts switch fell through to default');
    }
  }
}

const api = {
  init,
};

export default api;
