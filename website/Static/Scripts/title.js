$(function () {
    $('select').selectpicker();
    $('#search').data('actions-box', true);
    $('#search').val('').selectpicker('refresh');
    $('#search').selectpicker('destroy');
    $('#search').selectpicker();
});