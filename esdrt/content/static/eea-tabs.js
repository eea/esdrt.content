jQuery(document).ready(
	function($) {
    const setCurrentTab = () => {
      const allTabPanels = $(".eea-tabs-panel");
      allTabPanels.hide();

      let requestedPanel = window.location.hash ? $(document).find(window.location.hash) : null;
      if (!requestedPanel?.length) {
        requestedPanel = allTabPanels.first();
      }

      if (requestedPanel?.length) {
        requestedPanel.show();

        const requestedTabId = requestedPanel.attr('id')

        window.location.hash = requestedTabId;

        $(".eea-tabs > div").removeClass("active");
        $(`.eea-tabs a[href="#${requestedTabId}"]`).parent().addClass("active");
      }

    }
    setCurrentTab();
    $(window).bind('hashchange', setCurrentTab);
  });

