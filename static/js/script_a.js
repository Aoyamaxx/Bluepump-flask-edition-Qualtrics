(function () {

  function logSiteVisit(visitorId) {
    $.ajax({
      url: '/log_site_visit_a',
      method: 'POST',
      data: {
        visitor_id: visitorId,
      },
    });
  }

  function logSiteExit(visitor_id) {
  $.ajax({
    url: '/track_exit_a',
    method: 'POST',
    data: {
      visitor_id: visitor_id,
      last_page: location.pathname
    }
  });
}

  function fetchVisitorId(callback) {
    $.ajax({
      url: '/get_visitor_id_a',
      method: 'GET',
      success: function (response) {
        callback(response.visitor_id);
      },
    });
  }

  function trackDonateClick(visitorId, buttonType) {
    $.ajax({
      url: '/track_donate_click_a',
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

    $(document).on('click', '.donate, .donate-landing', function (event) {
      event.preventDefault();
      const buttonType = $(this).hasClass('donate-landing') ? 'index_a' : 'header_a';
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
        url: '/log_privacy_decision_a',
        method: 'POST',
        data: {
          visitor_id: serverVisitorId,
          decision: decision,
        },
      });
    });
  }

  $(document).ready(function () {
    $("#header-a").load("/header_a");
    $("#footer-a").load("/footer_a");
    $("#buttonDiv").load("/survey_button");

    if (typeof serverVisitorId !== 'undefined' && serverVisitorId !== '') {
      initializeEvents(serverVisitorId);
    } else {
      fetchVisitorId(function (visitorId) {
        initializeEvents(visitorId);
      });
    }

    $("#load-privacy-banner-a").load("/privacy_banner_a", function () {
      // After the content is loaded, append it to the body
      $('body').append($('#load-privacy-banner-a').html());
      $('#load-privacy-banner-a').remove();

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
        url: '/log_privacy_decision_a',
        method: 'POST',
        data: {
          visitor_id: serverVisitorId,
          decision: decision
        }
      });
    });

    $('#privacy-policy-link').on('click', function () {
      sessionStorage.setItem('privacy_decision', 'P');
      $('#privacy-banner-a').hide();
    });
  });
  });
})();