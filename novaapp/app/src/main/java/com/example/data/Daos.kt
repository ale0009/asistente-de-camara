package com.example.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface MissionDao {
    @Query("SELECT * FROM missions ORDER BY id ASC")
    fun getAllMissions(): Flow<List<Mission>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMission(mission: Mission)

    @Update
    suspend fun updateMission(mission: Mission)

    @Query("DELETE FROM missions WHERE id = :id")
    suspend fun deleteMission(id: Long)

    @Query("UPDATE missions SET isCompleted = 0")
    suspend fun resetAllMissions()

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(missions: List<Mission>)
}

@Dao
interface ActionLogDao {
    @Query("SELECT * FROM action_logs ORDER BY id DESC LIMIT 100")
    fun getRecentLogs(): Flow<List<ActionLogEntry>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLog(log: ActionLogEntry)

    @Query("DELETE FROM action_logs")
    suspend fun clearLogs()
}

@Dao
interface ObsidianNoteDao {
    @Query("SELECT * FROM obsidian_notes ORDER BY title ASC")
    fun getAllNotes(): Flow<List<ObsidianNote>>

    @Query("SELECT * FROM obsidian_notes WHERE title LIKE '%' || :query || '%' OR content LIKE '%' || :query || '%'")
    fun searchNotes(query: String): Flow<List<ObsidianNote>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNote(note: ObsidianNote)

    @Update
    suspend fun updateNote(note: ObsidianNote)
}
