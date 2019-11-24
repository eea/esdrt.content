(function(){

  function do_toggle(btn, elems, toggle) {
    var COOKIE = 'em.inbox.showempty';
    var cookie = docCookies.getItem(COOKIE) || 'hide';

    var action = toggle ? (cookie === 'show' ? 'hide' : 'show') : cookie;

    var btn_text;

    if (action === 'hide') {
      elems.fadeOut();
      btn_text = 'Expand view';
    }
    else if (action === 'show') {
      elems.fadeIn();
      btn_text = 'Collapse view';
    }

    btn.text(btn_text);

    if (toggle) {
      docCookies.setItem(COOKIE, action);
    }
  }

  function init_toggler(sel_targets, sel_button) {
    var targets =  $(sel_targets).filter(function(i, o){ return $('a', o).length === 0});
    var toggler = $(sel_button);

    if (targets.length > 0) {
      toggler.on('click', function(){
        do_toggle(toggler, targets, true);
      });
      do_toggle(toggler, targets, false);
      toggler.show();
    } else {
      toggler.remove();
    }

  }

  var ecsm = ecsm || {};

  ecsm.inbox = ecsm.inbox || {};
  ecsm.inbox.init_toggler = init_toggler;

  window.ecsm = ecsm;

})();
