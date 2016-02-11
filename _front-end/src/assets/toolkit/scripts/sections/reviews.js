import wanakana from '../vendor/wanakana.min';
import { revealToggle } from '../components/revealToggle';

//Grab CSRF token off of dummy form.
const CSRF = $('#csrf').val();

let KW,
    currentVocab,
    remainingVocab,
    startCount,
    correctTotal = 0,
    answeredTotal = 0,
    answerCorrectness = [],
    $reviewsLeft = $('#reviewsLeft'),
    $meaning = $('#meaning'),
    $streakIcon = $('.streak > .icon'),
    $ignoreButton = $('#ignoreAnswer'),
    $userID = $('#us-id'),
    $srsUp = $('#srsUp > .content'),
    $reviewsDone = $('#reviewsDone'),
    $reviewsCorrect = $('#reviewsCorrect'),
    $reveal = $('.reveal'),
    $answerPanel = $('#answerpanel'),
    $userAnswer = $('#userAnswer'),
    $detailKana = $('#detailKana'),
    $submitButton = $('#submitAnswer'),
    $detailKanji = $('#detailKanji'),
    $progressBar = $('.progress-bar > .value');

function init() {
  // if not on reviews page do nothing
  if (!/review/.test(window.location.pathname)) return;

  // set initial values
  KW = simpleStorage.get('KW');
  remainingVocab = window.KW.sessionVocab;
  startCount = remainingVocab.length;

  console.log('Settings:', KW.settings);

  $reviewsLeft.text(startCount - 1)
  currentVocab = remainingVocab.shift();
  $userID.val(currentVocab.user_specific_id);

  $detailKana.kana = $detailKana.find('.-kana');
  $detailKanji.kanji = $detailKanji.find('.-kanji');

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
  $detailKana.kana.html(currentVocab.readings.map(reading => `${reading} </br>`));
  $detailKanji.kanji.html(currentVocab.characters.map(kanji => `${kanji} </br>`));
}

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
  let answer = $userAnswer.val();
  let imeInput = false;

  if(answer === '') return;
  console.log('Comparing', answer, 'with vocab item:', currentVocab.meaning);

  //Fixing the terminal n.
  if (answer.endsWith('n')) {
    answer = answer.slice(0, -1) + 'ん';
  }
  //Ensure answer is full hiragana
  if (!wanakana.isHiragana(answer)) {
    let charCodesAnswer = [...answer].map(c => c.charCodeAt(0));
    // greater than basic latin [0-9Aa-Zz] etc and not in katakana charcode range
    // not explicitly checking for kanji here - but user shouldn't be entering spanish for example..!
    if (charCodesAnswer.every(x => x > 127 && x < 65345 || x > 65370)) {
      imeInput = true;
    } else {
      return nonHiraganaAnswer();
    }
  }

  const inReadings = () => $.inArray(answer, currentVocab.readings) != -1;
  const inCharacters = () => $.inArray(answer, currentVocab.characters) != -1;

  if (inReadings() || inCharacters()) {
    markRight();
    //Fills the correct kanji into the input field based on the user's answers
    if (!imeInput) {
      $userAnswer.val(currentVocab.characters[currentVocab.readings.indexOf(answer)]);
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

  enableButtons();
}

function processAnswer({correct} = {}) {
  let previouslyWrong,
      currentUserID = $userID.val();

  if (correct === true) {
    // Ensures this is the first time the vocab has been answered in this session, so it goes in the right container(incorrect/correct)
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = 1;
      previouslyWrong = false;
    } else {
      previouslyWrong = true;
    }
    correctTotal += 1;
    updateProgressBar(correctTotal / startCount * 100);

  } else if (correct === false) {
    answerCorrectness[currentUserID] = -1;
    previouslyWrong = true;
    currentVocab.streak -= 1;
    remainingVocab.push(currentVocab);
  }

  answeredTotal += 1;
  recordAnswer(currentUserID, correct, previouslyWrong); // record on server
}

function recordAnswer(userID, correctness, previouslyWrong) {
  $.post('/kw/record_answer/', {
      user_specific_id: userID,
      user_correct: correctness,
      csrfmiddlewaretoken: CSRF,
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
  $userID.val(currentVocab.user_specific_id);

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
