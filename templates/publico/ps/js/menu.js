(function ($) {

    $.fn.menumaker = function (options) {

        var cssmenu = $(this), settings = $.extend({title: "Menu", format: "dropdown", sticky: false}, options);

        return this.each(function () {
            cssmenu.prepend('<div id="menu-button" class="menu-button">' + settings.title + '</div>');
            $(this).find("#menu-button").on('click', function () {

                $(this).toggleClass('menu-opened');
                var mainmenu = $(this).next('ul');
                mainmenu.slideToggle();
            });

            cssmenu.find('li ul').parent().addClass('has-sub');

            multiTg = function () {
                cssmenu.find(".has-sub").prepend('<span class="submenu-button"></span>');
                cssmenu.find('.submenu-button').on('click', function () {
                    $(this).toggleClass('submenu-opened');
                    if ($(this).siblings('ul').hasClass('open')) {
                        $(this).siblings('ul').removeClass('open').hide();
                    }
                    else {
                        $(this).siblings('ul').addClass('open').show();
                    }
                });
            };

            if (settings.format === 'multitoggle')
                multiTg();
            else
                cssmenu.addClass('dropdown');

            if (settings.sticky === true)
                cssmenu.css('position', 'fixed');

            resizeFix = function () {
                if ($(window).width() > 1000) {
                    $("#menu-responsivo").removeClass('menu-aparecendo').addClass('menu-escondido');
                    $("#menu-original").removeClass('menu-escondido').addClass('menu-aparecendo');
                    $("#conteudo-original").removeClass('col-md-12').addClass('col-md-9');
                }
                if ($(window).width() <= 1000) {
                    $("#menu-original").removeClass('menu-aparecendo').addClass('menu-escondido');
                    $("#menu-responsivo").removeClass('menu-escondido').addClass('menu-aparecendo');
                    $("#conteudo-original").removeClass('col-md-9').addClass('col-md-12');
                    cssmenu.find('ul').hide().removeClass('open');
                }
            };
            resizeFix();
            return $(window).on('resize', resizeFix);

        });
    };
})(jQuery);