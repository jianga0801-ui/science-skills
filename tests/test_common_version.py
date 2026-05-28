import unittest


class CommonVersionTest(unittest.TestCase):
  def test_common_package_exposes_version(self):
    from skills import science_skills_common

    self.assertRegex(science_skills_common.__version__, r"^\d+\.\d+\.\d+")


if __name__ == "__main__":
  unittest.main()
