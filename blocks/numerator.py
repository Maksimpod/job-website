from flask import render_template


class NumeratorBlock:
  MAIN_TEMPLATE = 'blocks/numerator/main.html'
  LINK_ITEM_TEMPLATE = 'blocks/numerator/linkItem.html'
  EMPTY_ITEM_TEMPLATE = 'blocks/numerator/emptyItem.html'
  BLOCK_ALIGN = 'center'
  PAGE_NUMBER_PREFIX = 'page'
  BLOCKS_DIVIDER = "&nbsp;...&nbsp;\n"
  LINK_PART = '/'

  words = {
    'ru': { 'back': 'Назад', 'next': 'Вперед' },
    'en': { 'back': 'Back', 'next': 'Next' }
  }

  @staticmethod
  def makeNodePageNumber(pageNumber: int, prefix: str = '') -> str:
    return (f"{prefix}{pageNumber}" if (pageNumber > 0) else '')

  @staticmethod
  def __item(number: int = 1, current: int = 1, total: int = 1, prefix: str = '', baseURL: str = '', title: str = '') -> str:
    result = ''

    if (((number >= 0) and (number <= (total + 1))) and (current >= 1) and (current <= total)):
      parameters = {
        'title': (title if (title != '') else number),
        'href': baseURL +
          NumeratorBlock.LINK_PART +
          ##(NumeratorBlock.LINK_PART if (number > 1) else '') +
          NumeratorBlock.makeNodePageNumber(number, prefix)
          ##('' if (number == 1) else NumeratorBlock.makeNodePageNumber(number, prefix))
      }

      templateName = NumeratorBlock.EMPTY_ITEM_TEMPLATE

      if ((number != current) and (number >= 1) and (number <= total)):
        templateName = NumeratorBlock.LINK_ITEM_TEMPLATE

      result = render_template(templateName, **parameters)

    return result

  @staticmethod
  def __numerator(parameters: dict) -> str:
    result = ''

    if (parameters['pagesTotal'] > 1):
      if ((parameters['currentPage'] >= 1) and (parameters['currentPage'] <= parameters['pagesTotal'])):
        if ((parameters['sideLinksNumber'] >= 1) and (parameters['centerLinksNumber'] >= 3) and (parameters['centerLinksNumber'] % 2 == 1)):
          numberPrev = parameters['currentPage'] - 1
          numberNext = parameters['currentPage'] + 1

          result += NumeratorBlock.__item(numberPrev, parameters['currentPage'], parameters['pagesTotal'], parameters['pageNumberPrefix'],
            parameters['baseURL'], parameters['wordPrevious'])

          linksTotal = (parameters['sideLinksNumber'] * 2) + parameters['centerLinksNumber']

          if (parameters['pagesTotal'] > linksTotal):
            s = int((parameters['centerLinksNumber'] - 1) / 2)
            x = s + parameters['sideLinksNumber'] + 1
            z = parameters['pagesTotal'] - ((parameters['sideLinksNumber'] * 2) + parameters['centerLinksNumber'])

            showDotsLeft  = (parameters['currentPage'] > x)
            showDotsRight = (parameters['currentPage'] <= (parameters['pagesTotal'] - x))

            y = 0
            if (showDotsLeft):
              y = parameters['currentPage'] - s - parameters['sideLinksNumber'] - 1

            if (not(showDotsRight)):
              y = z

            i = 1

            while (i <= linksTotal):
              leftDotsPosition  = (i == (parameters['sideLinksNumber'] + 1))
              rightDotsPosition = (i == (parameters['sideLinksNumber'] + 1 + parameters['centerLinksNumber']))

              if ((showDotsLeft and leftDotsPosition) or (showDotsRight and rightDotsPosition)):
                result += parameters['blocksDivider']

              if (i <= parameters['sideLinksNumber']):
                k = i
              elif (i <= (parameters['sideLinksNumber'] + parameters['centerLinksNumber'])):
                k = i + y
              else:
                k = i + z

              result += NumeratorBlock.__item(k, parameters['currentPage'], parameters['pagesTotal'], parameters['pageNumberPrefix'],
                parameters['baseURL'])

              i += 1

          else:
            i = 1

            while (i <= parameters['pagesTotal']):
              result += NumeratorBlock.__item(i, parameters['currentPage'], parameters['pagesTotal'], parameters['pageNumberPrefix'],
                parameters['baseURL'])

              i += 1

          result += NumeratorBlock.__item(numberNext, parameters['currentPage'], parameters['pagesTotal'], parameters['pageNumberPrefix'],
            parameters['baseURL'], parameters['wordNext'])

    return result

  @staticmethod
  def __defaultParameters(parameters: dict) -> dict:
    language = 'ru'

    if ('pagesTotal' not in parameters):
      parameters['pagesTotal'] = 1
    elif (parameters['pagesTotal'] < 1):
      parameters['pagesTotal'] = 1

    if ('currentPage' not in parameters):
      parameters['currentPage'] = 1
    elif (parameters['pagesTotal'] < 1):
      parameters['currentPage'] = 1

      # 2k + 1, k > 0, k => N
    if ('centerLinksNumber' not in parameters):
      parameters['centerLinksNumber'] = 5
    elif (not((parameters['centerLinksNumber'] >= 3) and (parameters['centerLinksNumber'] % 2 == 1))):
      parameters['centerLinksNumber'] = 5

      # k, k > 0, k <= (parameters['pagesTotal'] - parameters['centerLinksNumber']) / 2
    if ('sideLinksNumber' not in parameters):
      parameters['sideLinksNumber'] = 2
    elif (not(parameters['sideLinksNumber'] <= ((parameters['pagesTotal'] - parameters['centerLinksNumber']) / 2))):
      parameters['sideLinksNumber'] = 2

    wordBack = (NumeratorBlock.words[language]['back'] if ('back' in NumeratorBlock.words[language]) else NumeratorBlock.words['ru']['back'])

    if ('wordPrevious' not in parameters):
      parameters['wordPrevious'] = wordBack
    elif (not(len(parameters['wordPrevious']) > 0)):
      parameters['wordPrevious'] = wordBack

    wordNext = (NumeratorBlock.words[language]['next'] if ('next' in NumeratorBlock.words[language]) else NumeratorBlock.words['ru']['next'])

    if ('wordNext' not in parameters):
      parameters['wordNext'] = wordNext
    elif (not(len(parameters['wordNext']) > 0)):
      parameters['wordNext'] = wordNext

    if ('blockAlign' not in parameters):
      parameters['blockAlign'] = NumeratorBlock.BLOCK_ALIGN
    elif (parameters['blockAlign'] not in ['left', 'right', 'center']):
      parameters['blockAlign'] = NumeratorBlock.BLOCK_ALIGN

    if ('pageNumberPrefix' not in parameters):
      parameters['pageNumberPrefix'] = NumeratorBlock.PAGE_NUMBER_PREFIX

    if ('baseURL' not in parameters):
      parameters['baseURL'] = '#'

    if ('blocksDivider' not in parameters):
      parameters['blocksDivider'] = NumeratorBlock.BLOCKS_DIVIDER
    elif (not(len(parameters['blocksDivider']) > 0)):
      parameters['blocksDivider'] = NumeratorBlock.BLOCKS_DIVIDER

    if ('linkLeftPart' not in parameters):
      parameters['linkLeftPart'] = NumeratorBlock.LINK_PART
    elif (not(len(parameters['linkLeftPart']) > 0)):
      parameters['linkLeftPart'] = NumeratorBlock.LINK_PART

    if ('linkRightPart' not in parameters):
      parameters['linkRightPart'] = NumeratorBlock.LINK_PART
    elif (not(len(parameters['linkRightPart']) > 0)):
      parameters['linkRightPart'] = NumeratorBlock.LINK_PART

    return parameters

  @staticmethod
  def create(parameters: dict = {}) -> str:
    defaultParameters = NumeratorBlock.__defaultParameters(parameters)
    defaultParameters['code'] = NumeratorBlock.__numerator(defaultParameters)

    return render_template(NumeratorBlock.MAIN_TEMPLATE, **defaultParameters)

  def __init__(self):
    raise RuntimeError('NumeratorBlock creation is forbidden')
