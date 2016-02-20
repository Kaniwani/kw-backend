import wanakana from '../vendor/wanakana.min';
import { revealToggle } from '../components/revealToggle';
import '../util/serializeObject';
import modals from '../vendor/modals';
modals.init({ backspaceClose: false });


// would really like to do a massive refactor, break out some functions as importable helpers
// undecided how I want to reorganise but it has become spaghetti and hard to reason about
// might use react just for reviews - since the template is only used to load in the review object
// instead we could load the page with a <div id="reactReview"></div> and ajax in the data
// and have much better organisation / handling of state


let KW,
    currentVocab,
    remainingVocab,
    startCount,
    correctTotal = 0,
    answeredTotal = 0,
    answerCorrectness = [],
    answer,
    $reviewsLeft = $('#reviewsLeft'),
    $meaning = $('#meaning'),
    $streakIcon = $('.streak > .icon'),
    $ignoreButton = $('#ignoreAnswer'),
    $srsUp = $('#srsUp > .content'),
    $reviewsDone = $('#reviewsDone'),
    $reviewsCorrect = $('#reviewsCorrect'),
    $reveal = $('.reveal'),
    $answerPanel = $('#answerpanel'),
    $userAnswer = $('#userAnswer'),
    $submitButton = $('#submitAnswer'),
    $detailKana = $('#detailKana'),
    $detailKanji = $('#detailKanji'),
    $progressBar = $('.progress-bar > .value');

// http://www.rikai.com/library/kanjitables/kanji_codes.unicode.shtml
// not including *half-width katakana / roman letters* since they should be considered typos
const japRegex = /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3400-\u4dbf]/;
const onlyJapaneseChars = str => [...str].every(c => japRegex.test(c));
//Grab CSRF token off of dummy form.
const CSRF = $('#csrf').val();

function init() {
  // if not on reviews page do nothing
  if (!/review/.test(window.location.pathname)) return;

  // set initial values
  KW = simpleStorage.get('KW');
  remainingVocab = window.KW.sessionVocab;
  startCount = remainingVocab.length;

  $reviewsLeft.text(startCount - 1)
  currentVocab = remainingVocab.shift();
  updateKanaKanjiDetails();
  updateStreak();

  // event listeners
  wanakana.bind($userAnswer.get(0));
  $userAnswer.keydown(handleShortcuts);

  // rotate or record on 'submit'
  $submitButton.click(enterPressed);
  $answerPanel.submit(enterPressed);
  $ignoreButton.click(ignoreAnswer);

  // ask a question
  $meaning.html(currentVocab.meaning);
  $userAnswer.focus();
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

  // if we went up a rank
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

// this can probably be an ajax followed by a window.navigate call I suppose instead of form jiggery
function makePost(path, params) {
  let form = document.createElement('form');
  form.setAttribute('method', 'post');
  form.setAttribute('action', path);
  form.setAttribute('class', '_visuallyhidden');

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


function compareAnswer() {
  answer = $userAnswer.val();
  let imeInput = false;

  if(answer === '') return;
  console.log('Comparing', answer, 'with vocab item: ');
  console.log(currentVocab);

  //Fixing the terminal n.
  if (answer.endsWith('n')) {
    answer = answer.slice(0, -1) + 'ん';
  }

  if (onlyJapaneseChars(answer)) {
    // user used japanese IME, proceed
    imeInput = true;
  } else if (!wanakana.isHiragana(answer)) {
    // user used english that couldn't convert to full hiragana - don't proceed
     return nonHiraganaAnswer();
  }

  const inReadings = () => $.inArray(answer, currentVocab.readings) != -1;
  const inCharacters = () => $.inArray(answer, currentVocab.characters) != -1;
  const getMatchedReading = (hiraganaStr) => currentVocab.characters[currentVocab.readings.indexOf(hiraganaStr)]

  if (inReadings() || inCharacters()) {
    markRight();
    //Fills the correct kanji into the input field based on the user's answers
    if (!imeInput) {
      $userAnswer.val(getMatchedReading(answer));
    }
    processAnswer({correct: true});
    if (KW.settings.autoAdvanceCorrect) setTimeout(() => enterPressed(), 900);
  }
  //answer was not in the known readings.
  else {
    markWrong();
    // don't processAnswer() here
    // wait for submission or ignore answer - which is handled by event listeners for submit/enter
    if (KW.settings.showCorrectOnFail) revealAnswers();

  }

  testSynonyms(currentVocab.user_specific_id);
  enableButtons();
}


// we're going to have to validate kana/kanji fields
// HAVE TO ADD NEW SYNONYM TO VOCAB ITEM BEFORE RETURNED TO REVIEW QUEUE
// also allow addition/deletion of synonyms in vocabulary in case user messed up

function testSynonyms(vocabID) {
  let $form = $('#synonymForm');
  let $button = $('#addSynonym');
  console.log($button);
  console.log($form);
  // temporary for now but should happen on wrong answer
  $button.removeClass('-hidden');

  $button.click(function(event) {
      console.log('event fired', event);
      // prepopulate
      $form.find('.wrappinglabel').each(function(i,el) {
        let $el = $(el);
        $el.find('.input').val('');
        $el.find('.jisho').removeClass('-ghost');
      });
      let $answerField = $(wanakana.isHiragana(answer) ? '#newKana' : '#newKanji');
      let $notAnswerField = $('.input').not($answerField);
      console.log($answerField, $notAnswerField)
      $answerField.val(answer).next('.jisho').addClass('-ghost');
      $notAnswerField.next('.jisho').attr({ href: `//jisho.org/search/${answer}` });
  });

  $form.submit(function(ev) {
    ev.preventDefault();
    let data = $(this).serializeObject();

    if (Object.keys(data).every(k => data[k] !== '' && onlyJapaneseChars(data[k]))) {
      addSynonym(vocabID, data);
      modals.closeModals();
    } else {
      /* form validation... */
    }
  });
}

function addSynonym(vocabID, {kana, kanji} = {}) {
  $.post('/kw/synonym/add', {
    csrfmiddlewaretoken: CSRF,
    user_specific_id: vocabID,
    kana: kana,
    kanji: kanji,
  })
  .always(res => {
    console.log(res);
    // should just clear vals and hide though to re-use instead of always creating new element
    $('#newAnswerSynonym').remove();
  });
}

function processAnswer({correct} = {}) {
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
      console.log(res);
    });
}

function ignoreAnswer() {
  $userAnswer.addClass('shake');
  setTimeout(() => rotateVocab({ignored: true}), 600);
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

function resetAnswerField() {
  clearColors();
  updateStreak();
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
  if (ignored) {
    // put ignored answer back onto end of review queue
    remainingVocab.push(currentVocab);
  }

  if (remainingVocab.length === 0) {
    console.log('Summary post data', answerCorrectness);
    return makePost('/kw/summary/', answerCorrectness);
  }

  currentVocab = remainingVocab.shift();

  if (correct) {
    $reviewsLeft.html(remainingVocab.length);
    $reviewsDone.html(correctTotal);
  }

  // guard against 0 / 0 (when first answer ignored)
  let percentCorrect = Math.floor((correctTotal / answeredTotal) * 100) || 0;
  console.log(`
    remainingVocab.length: ${remainingVocab.length},
    currentVocab: ${currentVocab.meaning},
    correctTotal: ${correctTotal},
    answeredTotal: ${answeredTotal},
    percentCorrect: ${percentCorrect}`
  );
  $reviewsCorrect.html(percentCorrect);
  $meaning.html(currentVocab.meaning);

  disableButtons();
  updateKanaKanjiDetails();
  resetAnswerField();
}

function enterPressed(event) {
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
  if (ev.which == 13) {
    ev.stopPropagation();
    ev.preventDefault();
    enterPressed(null);
  }
  if ($userAnswer.hasClass('-marked')) {
    ev.stopPropagation();
    ev.preventDefault();

    //Pressing P toggles phonetic reading
    if (ev.which == 80 || ev.which == 112) {
      revealAnswers({kana: true});
    }
    //Pressing K toggles the actual kanji reading.
    else if (ev.which == 75 || ev.which == 107) {
      revealAnswers({kanji: true});
    }
    //Pressing F toggles both item info boxes.
    else if (ev.which == 70 || ev.which == 102) {
      revealAnswers();
    }
    //Pressing I or backspace/del ignores answer when input has been marked incorrect
    else if (ev.which == 73 || ev.which == 105 || ev.which == 8 || ev.which == 46) {
      if ($userAnswer.hasClass('-incorrect')) ignoreAnswer();
    }
  }
}

const api = {
  init: init
};

export default api;
