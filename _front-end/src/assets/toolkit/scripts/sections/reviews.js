import wanakana from '../vendor/wanakana.min';
import { revealToggle } from '../components/revealToggle';
import '../util/serializeObject';
import modals from '../vendor/modals';
modals.init({ backspaceClose: false, callbackOpen: synonymModal });


// would really like to do a massive refactor, break out some functions as importable helpers
// undecided how I want to reorganise but it's becoming a spiderweb
// might use react just for reviews - since the template is only used to load in the review object
// instead we could load the page with a <div id="reactReview"></div> and ajax in the data
// and have much better organisation / handling of state


function debuglogger(...args) {
  if (window.KWDEBUG === true) {
    console.log(...args);
  }
}


let KW,
    currentVocab,
    remainingVocab,
    startCount,
    answer,
    correctTotal = 0,
    answeredTotal = 0,
    answerCorrectness = [],
    $homeLink = $('.homelink'),
    $reviewsLeft = $('#reviewsLeft'),
    $reviewsDone = $('#reviewsDone'),
    $reviewsCorrect = $('#reviewsCorrect'),
    $progressBar = $('.progress-bar > .value'),
    $meaning = $('#meaning'),
    $streakIcon = $('.streak > .icon'),
    $userAnswer = $('#userAnswer'),
    $answerPanel = $('#answerpanel'),
    $submitButton = $('#submitAnswer'),
    $ignoreButton = $('#ignoreAnswer'),
    $srsUp = $('#srsUp > .content'),
    $reveal = $('.reveal'),
    $detailKana = $('#detailKana'),
    $detailKanji = $('#detailKanji'),
    $synonymButton = $('#addSynonym'),
    $synonymForm = $('#synonymForm');


// http://www.rikai.com/library/kanjitables/kanji_codes.unicode.shtml
// not including *half-width katakana / roman letters* since they should be considered typos
const japRegex = /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3400-\u4dbf]/;
const onlyJapaneseChars = str => [...str].every(c => japRegex.test(c));
const onlyKanji = str => [...str].every(c => c.charCodeAt(0) >= 19968 && c.charCodeAt(0) < 40879);
//Grab CSRF token off of dummy form.
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
  updateStreak();

  // event listeners
  wanakana.bind(document.querySelector('#userAnswer'));
  wanakana.bind(document.querySelector('#newKana')); // new synonym form input
  wanakana.bind(document.querySelector('#newKanji')); // new synonym form input
  $userAnswer.keypress(handleShortcuts);

  // rotate or record on 'submit' rather than submitting form and page refreshing
  $submitButton.click(enterPressed);
  $answerPanel.submit(enterPressed);
  $ignoreButton.click(ignoreAnswer);

  // DEBUG
  $userAnswer.keypress(function(event) {
    debuglogger('kp', event.which, String.fromCharCode(event.which));
  });

  $synonymButton.click(synonymModal);
  $synonymForm.submit(handleSynonymForm);

  // ask a question
  $meaning.html(currentVocab.meaning);
  $userAnswer.focus();

  $homeLink.click(earlyTermination);
}

function getSrsRank(num) {
  return num > 8 ? 'burned' :
         num > 7 ? 'enlightened' :
         num > 5 ? 'master' :
         num > 2 ? 'guru' : 'apprentice';
}

function updateStreak() {
  let rank = getSrsRank(currentVocab.streak);
  $streakIcon.attr('class', `icon i-${rank}`)
  $streakIcon.closest('.streak').attr('data-hint', `${rank}`);
}

function streakLevelUp() {
  let rank = getSrsRank(currentVocab.streak);
  let newRank = getSrsRank(currentVocab.streak + 1);

  // TODO: sometimes a user gets an answer wrong, dropping them to 1/3 from 2/3 of a certain rank
  // Then when they get the answer correct later in the same review, we notice that they are at the
  // bottom level of a rank, and incorrectly assume they "ranked up" when really
  // they are still in the same belt as before they got it wrong
  // More data needs to be stored the item to properly determine how their rank changed
  if (newRank !== rank) {
    $srsUp.attr('data-after', newRank).addClass(`-animating -${newRank}`);
    $streakIcon.attr('class', `icon i-${newRank} -marked`)
               .closest('.streak').attr('data-hint', `${newRank}`);
  }
}

function updateKanaKanjiDetails() {
  $detailKana.find('.-kana').html(currentVocab.readings.map(reading => `${reading} </br>`));
  $detailKanji.find('.-kanji').html(currentVocab.characters.map(kanji => `${kanji} </br>`));
}

function earlyTermination(ev) {
  ev.preventDefault();
  postSummary('/kw/summary/', answerCorrectness);
}

function postSummary(path, params) {
  let form = document.createElement('form');
  form.setAttribute('method', 'post');
  form.setAttribute('action', path);
  form.setAttribute('class', 'u-visuallyhidden');

  for (let key in params) {
    if (params.hasOwnProperty(key)) {
      let hiddenField = document.createElement('input');
      hiddenField.setAttribute('type', 'hidden');
      hiddenField.setAttribute('name', key);
      hiddenField.setAttribute('value', params[key]);

      form.appendChild(hiddenField);
    }
  }
  //CSRF hackery.
  let csrf_field = document.createElement('input');
  csrf_field.setAttribute('name', 'csrfmiddlewaretoken');
  csrf_field.setAttribute('value', CSRF);
  form.appendChild(csrf_field);
  document.body.appendChild(form);
  form.submit();
}

String.prototype.endsWith = function(suffix) {
  return this.indexOf(suffix, this.length - suffix.length) !== -1;
};

String.prototype.startsWith = function(prefix) {
  return this.slice(0, prefix.length) === prefix;
};

// Fixing the terminal n.
function addTerminalN(str) {
  if (str.endsWith('n')) answer = str.slice(0, -1) + 'ん';
}

// Add tilde to ime input
function addStartingTilde(str) {
  const tildeJA = '〜';
  const tildeEN = '~';
  if (str.startsWith(tildeEN)) answer = tildeJA + str.slice(1);
  if (!str.startsWith(tildeJA)) answer = tildeJA + str;
}

function emptyString(str) {
  return str === '';
}

function compareAnswer() {
  debuglogger('compareAnswer called');
  let imeInput = false;
  answer = $userAnswer.val().trim();

  if (emptyString(answer)) return;

  debuglogger('Comparing', answer, 'with vocab item:')
  if (window.KWDEBUG === true) console.table(currentVocab);

  addTerminalN(answer);

  if (onlyJapaneseChars(answer)) {
    // user used japanese IME, proceed
    imeInput = true;
    if (currentVocab.characters[0].startsWith('〜') && onlyKanji(answer)) addStartingTilde(answer);

  } else if (!wanakana.isHiragana(answer)) {
    // user used english that couldn't convert to full hiragana - don't proceed
    return nonHiraganaAnswer();
  }

  const inReadings = () => $.inArray(answer, currentVocab.readings) != -1;
  const inCharacters = () => $.inArray(answer, currentVocab.characters) != -1;
  const getMatchedReading = (hiraganaStr) => currentVocab.characters[currentVocab.readings.indexOf(hiraganaStr)]

  if (inReadings() || inCharacters()) {
    let advanceDelay = 850;
    markRight();
    processAnswer({correct: true});
    //Fills the correct kanji into the input field based on the user's answers
    if (wanakana.isHiragana(answer)) $userAnswer.val(getMatchedReading(answer));
    if (KW.settings.showCorrectOnSuccess) {
      revealAnswers();
      if (KW.settings.autoAdvanceCorrect) advanceDelay = 1400;
    }
    if (KW.settings.autoAdvanceCorrect) setTimeout(() => enterPressed(null, true), advanceDelay);
  }
  //answer was not in the known readings.
  else {
    markWrong();
    // don't processAnswer() here
    // wait for submission or ignore answer - which is handled by event listeners for submit/enter
    if (KW.settings.showCorrectOnFail) revealAnswers();
  }

  enableButtons();
}

function synonymModal() {
  debuglogger('synonymModal called');
  let $form = $('#synonymForm');
  let $answerField = $(wanakana.isHiragana(answer) ? '#newKana' : '#newKanji');
  let $notAnswerField = $('.input').not($answerField);

  // prepopulate
  $form.find('.wrappinglabel').each(function(i,el) {
    let $el = $(el);
    $el.find('.input').val('');
    $el.find('.jisho').removeClass('-ghost');
  });

  $answerField.val(answer).next('.jisho').addClass('-ghost');
  $notAnswerField.next('.jisho').attr({ href: `http://jisho.org/search/${answer}` });

  setTimeout(() => $notAnswerField.focus(), 200);
}

function handleSynonymForm(ev) {
  debuglogger('handleSynonymForm called');
  ev.preventDefault();
  let $this = $(this);
  let vocabID = currentVocab.user_specific_id;
  let $submitButton = $this.find('#synonymSubmit');
  let $validation = $this.find('.validation');
  let data = $this.serializeObject();

  if (Object.keys(data).every(k => data[k] !== '' && onlyJapaneseChars(data[k]))) {
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

function addSynonym(vocabID, {kana, kanji} = {}) {
  // add for when in-memory item is returned to review queue
  currentVocab.readings.push(kana);
  currentVocab.characters.push(kanji);

  // save on server
  $.post('/kw/synonym/add', {
    csrfmiddlewaretoken: CSRF,
    user_specific_id: vocabID,
    kana: kana,
    kanji: kanji,
  })
  .always(res => {
    debuglogger(res);
  });
}

function processAnswer({correct} = {}) {
  debuglogger('processAnswer called')
  let previouslyWrong,
      currentvocabID = currentVocab.user_specific_id;

  if (correct === true) {
    // Ensures this is the first time the vocab has been answered in this session, so it goes in the right container(incorrect/correct)
    if ($.inArray(currentvocabID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentvocabID] = 1;
      previouslyWrong = false;
    } else {
      previouslyWrong = true;
    }
    correctTotal += 1;
    updateProgressBar(correctTotal / startCount * 100);

  } else if (correct === false) {
    answerCorrectness[currentvocabID] = -1;
    previouslyWrong = true;
    currentVocab.streak -= 1;
    remainingVocab.push(currentVocab);
  }

  answeredTotal += 1;
  recordAnswer(currentvocabID, correct, previouslyWrong); // record on server
}

function recordAnswer(vocabID, correctness, previouslyWrong) {
  $.post('/kw/record_answer/', {
      csrfmiddlewaretoken: CSRF,
      user_specific_id: vocabID,
      user_correct: correctness,
      wrong_before: previouslyWrong
    })
    .always(res => {
      debuglogger(res);
    });
}

function ignoreAnswer({ animate = true } = {}) {
  debuglogger('ignoreAnswer called')
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

function markWrong() {
  clearColors();
  $userAnswer.addClass('-marked -incorrect');
  $streakIcon.addClass('-marked');
  $ignoreButton.removeClass('-hidden');
  $synonymButton.removeClass('-hidden');
}

function markRight() {
  clearColors();
  $userAnswer.addClass('-marked -correct');
  $streakIcon.addClass('-marked');
  streakLevelUp();
}

function updateProgressBar(percent) {
  $progressBar.css('width', percent + '%');
}

function resetQuizUI() {
  clearColors();
  updateStreak();
  disableButtons();
  updateKanaKanjiDetails();
  $srsUp.removeClass('-animating');
  $userAnswer.removeClass('shake');
  $userAnswer.val('');
  $userAnswer.focus();
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

function revealAnswers({kana, kanji} = {}) {
  if (!!kana) revealToggle($detailKana.find('.button'));
  else if (!!kanji) revealToggle($detailKanji.find('.button'));
  else {
    revealToggle($detailKana.find('.button'));
    revealToggle($detailKanji.find('.button'));
  }
}

function rotateVocab({ignored = false, correct = false} = {}) {
  debuglogger('rotateVocab called')
  if (ignored) {
    // put ignored answer back onto end of review queue
    remainingVocab.push(currentVocab);
  }

  if (remainingVocab.length === 0) {
    // debuglogger('Summary post data', answerCorrectness);
    return postSummary('/kw/summary/', answerCorrectness);
  }

  currentVocab = remainingVocab.shift();

  if (correct) {
    $reviewsLeft.html(remainingVocab.length);
    $reviewsDone.html(correctTotal);
  }

  // guard against 0 / 0 (when first answer ignored)
  let percentCorrect = Math.floor((correctTotal / answeredTotal) * 100) || 0;
  // debuglogger(`
  //   remainingVocab.length: ${remainingVocab.length},
  //   currentVocab: ${currentVocab.meaning},
  //   correctTotal: ${correctTotal},
  //   answeredTotal: ${answeredTotal},
  //   percentCorrect: ${percentCorrect}`
  // );

  // TODO: this is slightly off if user ignored incorrect answer - need to account for that
  $reviewsCorrect.html(percentCorrect);
  $meaning.html(currentVocab.meaning);

  resetQuizUI();
}

function enterPressed(event, auto = false) {
  debuglogger('eP:', event, 'auto?', auto);
  if (event != null) {
    event.stopPropagation();
    event.preventDefault();
  }

  if ($userAnswer.hasClass('-marked')) {
    if ($userAnswer.hasClass('-correct')) {
      rotateVocab({correct: true});
    } else if($userAnswer.hasClass('-incorrect')) {
      processAnswer({correct: false});
      rotateVocab({correct: false});
    }
  } else {
    compareAnswer();
  }
}

function handleShortcuts(ev) {
  if (ev.which === 13) {
    debuglogger('handleShortcuts: not -marked, 13;')
    ev.stopPropagation();
    ev.preventDefault();
    enterPressed(null);
  } else if ($userAnswer.hasClass('-marked')) {
    debuglogger('handleShortcuts: -marked, not 13;')
    ev.stopPropagation();
    ev.preventDefault();

    switch(true) {
      // Pressing P toggles phonetic reading
      case (ev.which === 80 || ev.which === 112):
        debuglogger('case: P', 'event was:', ev);
        revealAnswers({kana: true});
        break;
      // Pressing K toggles the actual kanji reading.
      case (ev.which === 75 || ev.which === 107):
        debuglogger('case: K', 'event was:', ev);
        revealAnswers({kanji: true});
        break;
      // Pressing F toggles both item info boxes.
      case (ev.which === 70 || ev.which === 102):
        debuglogger('case: F', 'event was:', ev);
        revealAnswers();
        break;
      // Pressing S toggles both add synonym modal.
      case (ev.which === 83 || ev.which === 115):
        debuglogger('case: S', 'event was:', ev);
        modals.openModal(null, '#newSynonym', {
          backspaceClose: false, callbackOpen: synonymModal
        });
        break;
      // Pressing I ignores answer when input has been marked incorrect
      case (ev.which === 73 || ev.which === 105):
        debuglogger('case: I', 'event was:', ev);
        if ($userAnswer.hasClass('-incorrect')) ignoreAnswer();
        break;
      default:
        debuglogger('switch through to default');
    }
  }
}


const api = {
  init: init
};

export default api;
