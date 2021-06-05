from rest_framework import serializers

from follow_up.models import Panel2CognitiveTest
from medical_test.models import CognitiveTest, Question, Answer, PatientResponse


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        exclude = ('question',)


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'label','type', 'answers')


class CognitiveTestSerializerFull(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = CognitiveTest
        fields = ('id', 'name','type','url', 'description','logo', 'questions')


class CognitiveTestSerializerWithoutQA(serializers.ModelSerializer):
    class Meta:
        model = CognitiveTest
        fields = ('id', 'name','type','url' ,'description','logo')


class Panel2CognitiveTestSerializer(serializers.ModelSerializer):
    CognitiveTest = CognitiveTestSerializerWithoutQA(read_only=True)

    class Meta:
        model = Panel2CognitiveTest
        fields = ('id', 'done', 'CognitiveTest', 'response_time')


# class PatientResponseSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model=PatientResponse
#         fields="__all__"
#
# class PatientResponseSerializer(serializers.ModelSerializer):
#     test_name = serializers.CharField(source="CognitiveTest.name", read_only=True)
#     question = serializers.CharField(source="question.label", read_only=True)
#     answer = serializers.CharField(source="Answer.text", read_only=True)
#     score = serializers.CharField(source="Answer.score", read_only=True)
#
#     class Meta:
#         model = PatientResponse
#         fields = ("id", "test_name", "question", "answer", "score")
class PatientResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientResponse
        fields = ("Answer", "question","description")


class AnsweredTestPanelSerializer(serializers.ModelSerializer):
    test_id = serializers.IntegerField(source="CognitiveTest.id", read_only=True)
    name = serializers.CharField(source="CognitiveTest.name", read_only=True)
    description = serializers.CharField(source="CognitiveTest.description", read_only=True)
    logo = serializers.CharField(source="CognitiveTest.logo", read_only=True)
    panel_id = serializers.CharField(source="panel.id", read_only=True)


    class Meta:
        model = Panel2CognitiveTest
        fields = ("id","test_id", "name", "description","logo", "done","panel_id","time_add_test")
        read_only_fields = ['id']



class AnsweredTestSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="CognitiveTest.id", read_only=True)
    name = serializers.CharField(source="CognitiveTest.name", read_only=True)
    description = serializers.CharField(source="CognitiveTest.description", read_only=True)

    class Meta:
        model = PatientResponse
        fields = ("id", "name", "description")
