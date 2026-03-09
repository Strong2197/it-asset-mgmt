from django.shortcuts import redirect, render


def save_model_form(request, *, form_class, template_name, success_url, instance=None, title=''):
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(success_url)
    else:
        form = form_class(instance=instance)

    return render(request, template_name, {'form': form, 'title': title})


def delete_on_post(request, *, obj, success_url):
    if request.method == 'POST':
        obj.delete()
    return redirect(success_url)
