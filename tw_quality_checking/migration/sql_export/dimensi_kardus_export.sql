SELECT
'tw_selection_' || REPLACE(quest.type, 'DimensiKardus', 'CardboardDimensions') || '_' || quest.internal_value::varchar as "external_id",
REPLACE(quest.name, ',', '.') as "name",
REPLACE(quest.type, 'DimensiKardus', 'CardboardDimensions') as "type",
COALESCE(quest.value,REPLACE(quest.name, ',', '.')) as "value",
quest.internal_value as "internal_value",
quest.active as "active"
FROM dms_questionnaire quest
WHERE quest.type = 'DimensiKardus'