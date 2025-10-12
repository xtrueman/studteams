// FAQ page JavaScript - дополнительная интерактивность

$(document).ready(function() {
    // Добавляем плавную прокрутку к якорю при открытии аккордеона
    $('.accordion-button').on('click', function() {
        setTimeout(() => {
            const target = $(this).attr('data-bs-target');
            if ($(target).hasClass('show')) {
                $('html, body').animate({
                    scrollTop: $(this).offset().top - 100
                }, 300);
            }
        }, 350);
    });

    // Подсветка активного элемента навигации
    $('.nav-link[href="/faq"]').addClass('active');
});
