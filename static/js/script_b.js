(function () {

  function logSiteVisit(visitorId) {
    $.ajax({
      url: '/log_site_visit_b',
      method: 'POST',
      data: {
        visitor_id: visitorId,
      },
    });
  }

  function logSiteExit(visitor_id) {
  $.ajax({
    url: '/track_exit_b',
    method: 'POST',
    data: {
      visitor_id: visitor_id,
      last_page: location.pathname
    }
  });
}

  function fetchVisitorId(callback) {
    $.ajax({
      url: '/get_visitor_id_b',
      method: 'GET',
      success: function (response) {
        callback(response.visitor_id);
      },
    });
  }

  function trackDonateClick(visitorId, buttonType) {
    $.ajax({
      url: '/track_donate_click_b',
      method: 'POST',
      data: {
        visitor_id: visitorId,
        button_type: buttonType
      }
    });
  }

  function initializeEvents(visitorId) {
    let startTimeGlobal = new Date();

    // Log the site visit and set the visitor_id in sessionStorage
    logSiteVisit(visitorId);
    sessionStorage.setItem('visitor_id', visitorId);

    window.addEventListener('beforeunload', () => {
      logSiteExit(visitorId);
    });

    // Event listeners and other code that depends on visitorId
    $('.close, .not-now').on('click', function () {
      hideDonatePopup();
      trackUserAction(visitorId, 'closed_popup_no');
    });

    $('body').on('click', '#donate-button', function () {
      hideDonatePopup();
      trackUserAction(visitorId, 'clicked_donate');
    });

    $('body').on('click', '#donate-popup .not-now', function () {
      trackUserAction(visitorId, 'closed_popup_not_now');
    });

    $('body').on('click', '#donate-popup .close', function () {
      trackUserAction(visitorId, 'closed_popup_close');
    });

    $('body').on('click', '#learn-more-link', function () {
      trackUserAction(visitorId, 'clicked_learn_more');
    });

    $(document).on('click', '.donate, .donate-landing', function (event) {
      event.preventDefault();
      const buttonType = $(this).hasClass('donate-landing') ? 'index_b' : 'header_b';
      const visitorId = sessionStorage.getItem('visitor_id');
      trackDonateClick(visitorId, buttonType);
      window.location.href = $(this).attr('href');
    });

    $('#accept-privacy, #reject-privacy').on('click', function () {
      const decision = this.id === 'accept-privacy' ? 'Y' : 'N';
      sessionStorage.setItem('privacy_decision', decision);
      $('#privacy-banner').hide();

      // Record user decision in your database
      $.ajax({
        url: '/log_privacy_decision_b',
        method: 'POST',
        data: {
          visitor_id: serverVisitorId,
          decision: decision,
        },
      });
    });
  }

  function trackUserAction(visitorId, action) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/track_user_action_b', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send(`visitor_id=${visitorId}&action=${action}`);
  }

  function showDonatePopup() {
  console.log('Showing popup');
  $('#donate-popup').fadeIn(300);
  }

  function hideDonatePopup() {
    $('#donate-popup').fadeOut(300);
  }

  let timeElapsed = 0;
  const timeToShowPopup = 10000;

  function checkUserAction() {
    timeElapsed += 1000;
    console.log("Time elapsed:", timeElapsed);

    // Check if the popup has already been shown
    const popupShown = sessionStorage.getItem('popup_shown');

    if (timeElapsed >= timeToShowPopup && !popupShown) {
      showDonatePopup();

      // Set a flag in sessionStorage to indicate the popup has been shown
      sessionStorage.setItem('popup_shown', true);
    }
  }

  $(document).ready(function () {
    $("#header-b").load("/header_b");
    $("#footer-b").load("/footer_b");
    $("#buttonDiv").load("/survey_button");

    if (typeof serverVisitorId !== 'undefined' && serverVisitorId !== '') {
      initializeEvents(serverVisitorId);
    } else {
      fetchVisitorId(function (visitorId) {
        initializeEvents(visitorId);
      });
    }

    $("#load-privacy-banner-b").load("/privacy_banner_b", function () {
      // After the content is loaded, append it to the body
      $('body').append($('#load-privacy-banner-b').html());
      $('#load-privacy-banner-b').remove();

      // Only show the privacy banner if the user hasn't made a decision yet
      if (!sessionStorage.getItem('privacy_decision')) {
        $('#privacy-banner').show();
      }

    // Handle privacy banner actions
    $('body').on('click', '#accept-privacy, #reject-privacy', function () {
      const decision = this.id === 'accept-privacy' ? 'Y' : 'N';
      const visitorId = sessionStorage.getItem('visitor_id');
      sessionStorage.setItem('privacy_decision', decision);
      $('#privacy-banner').hide();

     // Record user decision in your database
      $.ajax({
        url: '/log_privacy_decision_b',
        method: 'POST',
        data: {
          visitor_id: serverVisitorId,
          decision: decision
        }
      });
    });

    $('#privacy-policy-link').on('click', function () {
      sessionStorage.setItem('privacy_decision', 'P');
      $('#privacy-banner-b').hide();
    });

    // Load the donate_popup content
    $('#load-donate-popup-b').load('/donate_popup_b', function () {
      // After the content is loaded, append it to the body
      $('body').append($('#load-donate-popup-b').html());
      $('#load-donate-popup-b').remove();

      // Add the event listeners for closing the popup and clicking the donate button
      $('.close, .not-now').on('click', function () {
        hideDonatePopup();
      });
    });

    // Check if the user is on the donate page or clicked the donate button within 15 seconds
    const checkUserActionInterval = setInterval(checkUserAction, 1000);
  });
  });
})();