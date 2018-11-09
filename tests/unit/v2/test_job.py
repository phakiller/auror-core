#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import shutil, tempfile
from unittest import TestCase
from auror.v2.job import Job, Command, Spark, Python, Email


class JobTest(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp() # Create a temporary directory
        self.data_job = Job("test_job_name", None, ["other_job_name"], None,
                           {"executor.cores": "2", "driver.memory": "6g"})

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True) # Remove the directory after the test

    def test_get_instances(self):
        instance_job = self.data_job.instance("test_job_name_x", None, ["other_job_name_x"], None, {"executor.cores": "2"})

        self.assertIsInstance(instance_job, Job)

    def test_as_type(self):
        expected = "python"
        content = self.data_job.as_type(Python)
        actual = content._type

        self.assertEqual(expected, actual)

    def test_with_name(self):
        expected = "test_job_name_x"
        content = self.data_job.with_name("test_job_name_x")
        actual = content.name

        self.assertEqual(expected, actual)

    def test_with_dependencies(self):
        data_job = Job("test_job_name_2", ["test_job_name_2"], {"driver.memory": "5g"})
        content = self.data_job.with_dependencies(data_job)
        expected = ["test_job_name_2"]
        actual = content.dependencies

        self.assertEqual(expected, actual)

    def test_with_method(self):
        extra = {"env.HADOOP_USER_NAME": "hadoop", "spark.version": "1.0.0"}
        content = self.data_job.with_(**extra)
        expected = {"executor.cores": "2", "driver.memory": "6g", "env.HADOOP_USER_NAME": "hadoop", "spark.version": "1.0.0"}
        actual = content.extra

        self.assertEqual(expected, actual)

    def test_write_in_folder(self):
        content = self.data_job.as_type(Python)
        content._add_items()
        content._write(self.test_dir)
        f = open(path.join(self.test_dir, path.basename(self.test_dir)+".flow"))
        expected = "#test_job_name.job\ndependencies=other_job_name\ndriver.memory=6g\nexecutor.cores=2\ntype=python\n"

        self.assertEqual(f.read(), expected)
        f.close()

    def test_add_items_and_it_contains_one_dependency(self):
        content = self.data_job.as_type(Python)
        content._add_items()

        self.assertEqual("other_job_name", content.properties["nodes"][0]["dependsOn"][0])
        self.assertEqual("python", content.properties["nodes"][0]["type"])
        self.assertEqual("2", content.properties["nodes"][0]["executor.cores"])
        self.assertEqual("6g", content.properties["nodes"][0]["driver.memory"])

    def test_add_items_and_it_contains_two_dependencies(self):
        data_job = Job("test_job_name", [], {})
        data_job_2 = Job("test_job_name_2", [], {})
        content = self.data_job.with_dependencies(data_job, data_job_2).as_type(Spark)
        content._add_items()

        self.assertEqual("test_job_name,test_job_name_2", content.dependencies)
        self.assertEqual("command", content.properties["nodes"][0]["type"])
        self.assertEqual("2", content.properties["nodes"][0]["config"]["executor.cores"])
        self.assertEqual("6g", content.properties["nodes"][0]["config"]["driver.memory"])

    def test_add_items_and_it_does_not_contain_dependencies(self):
        data_job_x = Job("name_teste_job_4", None, [], None, {"spark.version": "1.0.1"})
        content = data_job_x.as_type(Python)
        content._add_items()

        self.assertEqual([], content.properties["nodes"][0]["dependsOn"])
        self.assertEqual("python", content.properties["nodes"][0]["type"])


class CommandJobTest(TestCase):

    def test_with_all_default(self):
        expected = Job("test_job_name", None, ["other_job_name"], None,
                            {"executor.cores": "2", "driver.memory": "6g"})

        self.assertIsInstance(expected, Job)

    def test_with_command(self):
        command = "${python} -c 'from teste import teste_command_spark; teste_command_spark()'"
        result = Command().with_command(command=command)
        actual = result.extra
        expected = {'command': "${python} -c 'from teste import teste_command_spark; teste_command_spark()'"}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_another_command_without_a_command(self):
        command = "${python} -c 'from teste import teste_command_spark; teste_command_spark()'"
        result = Command().with_another_command(command=command)
        actual = result.extra
        expected = {'command': "${python} -c 'from teste import teste_command_spark; teste_command_spark()'"}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_another_command_where_a_command_already_exists(self):
        command_ = "${python} -c 'from teste import teste_command_spark; teste_command_spark()'"
        result_ = Command().with_another_command(command=command_)
        command = "${python} -c 'from teste import teste_command_spark_again; teste_command_spark_again()'"
        result = result_.with_another_command(command=command)
        actual = result.extra
        expected = {'command': "${python} -c 'from teste import teste_command_spark; teste_command_spark()'", 
                    'command.1': "${python} -c 'from teste import teste_command_spark_again; teste_command_spark_again()'"}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)


class SparkJobTest(TestCase):

    def test_with_all_default(self):
        result = Spark().with_all_default()
        actual = result.extra
        expected = {'spark.version': '2.2.1', 'driver.memory': '1g', 'queue': 'default',
                    'num.executors': '1', 'env.HADOOP_USER_NAME': 'hadoop', 'executor.memory': '1g',
                    'executor.cores': '1'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_hadoop_user(self):
        result = Spark().with_hadoop_user(hadoop_user='teste')
        actual = result.extra
        expected = {'env.HADOOP_USER_NAME': 'teste'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_spark_version(self):
        result = Spark().with_spark_version(spark_version='1.0.0')
        actual = result.extra
        expected = {'spark.version': '1.0.0'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_queue(self):
        result = Spark().with_queue(queue='teste')
        actual = result.extra
        expected = {'queue': 'teste'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_driver_memory(self):
        result = Spark().with_driver_memory(driver_memory='1g')
        actual = result.extra
        expected = {'driver.memory': '1g'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_executor_memory(self):
        result = Spark().with_executor_memory(executor_memory='1g')
        actual = result.extra
        expected = {'executor.memory': '1g'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_executor_cores(self):
        result = Spark().with_executor_cores(executor_cores='1')
        actual = result.extra
        expected = {'executor.cores': '1'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_dynamic_allocation(self):
        result = Spark().with_dynamic_allocation(min_executors='1', max_executors='5')
        actual = result.extra
        expected = {"conf.spark.dynamicAllocation.enabled": "true", \
                    "min.executors": '1', "max.executors": '5'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_num_executors(self):
        result = Spark().with_num_executors(num_executors='1')
        actual = result.extra
        expected = {'num.executors': '1'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_jar_file(self):
        result = Spark().with_jar_file(jar_file='teste/jar/teste-jar-file.jar')
        actual = result.extra
        expected = {'jar.file': 'teste/jar/teste-jar-file.jar'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_extra_jars(self):
        result = Spark().with_extra_jars(extra_jars='hdfs\:///spark/teste-jar-1-1.0.0.jar,hdfs\:///spark/teste-jar-2-1.0.0.jar')
        actual = result.extra
        expected = {'extra.jars': 'hdfs\:///spark/teste-jar-1-1.0.0.jar,hdfs\:///spark/teste-jar-2-1.0.0.jar'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_java_class(self):
        result = Spark().with_java_class(java_class='com.globo.ab.jobs.teste.SparkJob')
        actual = result.extra
        expected = {'java.class': 'com.globo.ab.jobs.teste.SparkJob'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_with_args(self):
        result = Spark().with_args(some_args='${date} teste-prod teste-yarn')
        actual = result.extra
        expected = {'args': '${date} teste-prod teste-yarn'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_before_add_hook_without_extra_jars(self):
        result = Spark().before_add_hook()
        actual = result.extra
        expected = {'command': '${spark.submit}'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)

    def test_before_add_hook_with_extra_jars(self):
        result_extra = Spark().with_extra_jars(extra_jars='hdfs\:///spark/teste-jar-1-1.0.0.jar,hdfs\:///spark/teste-jar-2-1.0.0.jar')
        result = result_extra.before_add_hook()
        actual = result.extra
        expected = {'command': '${spark.submit.extra.jars}', 'extra.jars': 'hdfs\\:///spark/teste-jar-1-1.0.0.jar,hdfs\\:///spark/teste-jar-2-1.0.0.jar'}

        self.assertEqual('command', result._type)
        self.assertEqual(expected, actual)     


class PythonJobTest(TestCase):

    def test_with_all_default(self):
        result = Python().with_all_default()
        actual = result.extra
        expected = {'python': '${python3}', 'virtualenv.requirements': './requirements.txt'}

        self.assertEqual('python', result._type)
        self.assertEqual(expected, actual)

    def test_with_python(self):
        result = Python().with_python(python='${python}')
        actual = result.extra
        expected = {'python': '${python}'}

        self.assertEqual('python', result._type)
        self.assertEqual(expected, actual)

    def test_with_virtualenv(self):
        result = Python().with_virtualenv(virtualenv='teste')
        actual = result.extra
        expected = {'virtualenv': 'teste'}

        self.assertEqual('python', result._type)
        self.assertEqual(expected, actual)

    def test_with_requirements(self):
        result = Python().with_requirements(requirements="./teste.txt")
        actual = result.extra
        expected = {'virtualenv.requirements': './teste.txt'}

        self.assertEqual('python', result._type)
        self.assertEqual(expected, actual)  


class EmailJobTest(TestCase):

    def test_with_subject(self):
        result = Email().with_subject("Exemplo de email")
        actual = result.extra
        expected = {"mail.subject": "Exemplo de email"}

        self.assertEqual("email", result._type)
        self.assertEqual(expected, actual)

    def test_with_message(self):
        result = Email().with_message("Esse é o conteúdo do email")
        actual = result.extra
        expected = {"mail.message": "Esse é o conteúdo do email"}

        self.assertEqual("email", result._type)
        self.assertEqual(expected, actual)

    def test_with_to_recipient(self):
        result = Email().with_to_recipient("exemplo@corp.globo.com")
        actual = result.extra
        expected = {"mail.to": "exemplo@corp.globo.com"}

        self.assertEqual("email", result._type)
        self.assertEqual(expected, actual)

    def test_message_with_broken_lines(self):
        mail_message = "Esse é o conteúdo do email"
        result_ = Email().message_with_broken_lines(mail_message)
        mail_message_2 = "Essa é uma nova linha"
        result_2 = result_.message_with_broken_lines(mail_message_2)
        mail_message_3 = "Pode ser inseridas quantas linhas quiser"
        result_3 = result_2.message_with_broken_lines(mail_message_3)

        actual = result_3.extra
        expected = {"mail.message.1": "Esse é o conteúdo do email",
                    "mail.message.2": "Essa é uma nova linha",
                    "mail.message.3": "Pode ser inseridas quantas linhas quiser"}

        self.assertEqual("email", result_3._type)
        self.assertEqual(expected, actual)

    def test_in_which_email_is_not_sent(self):
        result = Email().with_send("false")
        actual = result.extra
        expected = {"mail.send": "false"}

        self.assertEqual("email", result._type)
        self.assertEqual(expected, actual)
