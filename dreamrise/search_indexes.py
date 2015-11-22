import datetime
from haystack import indexes
from dreamrise.models import Activity


class ActivityIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    # pub_date = indexes.DateTimeField(model_attr='pub_date')

    def get_model(self):
        return Activity

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()