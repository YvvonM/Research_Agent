import sqlite3
import json
from datetime import datetime
import uuid
from typing import Dict, List, Optional

class ResearchDatabase:
    def __init__(self, db_path="Research.db"):
        self.db_path = db_path
        self._setup()

    

    def _setup(self):
        """Initialize the databse with all the necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        #session table
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions(
                       session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                metadata TEXT  -- JSON field for additional session data
                       )''')
        #research queries table
        cursor.execute('''CREATE TABLE IF NOT EXISTS research_queries(
                query_id TEXT PRIMARY KEY,
                session_id TEXT,
                original_query TEXT NOT NULL,
                generated_queries TEXT,  -- JSON array of generated queries
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id))''')

        #Research structure table
        cursor.execute('''CREATE TABLE IF NOT EXISTS research_structure(
                      structure_id TEXT PRIMARY KEY,
                query_id TEXT,
                session_id TEXT,
                structure_data TEXT,  -- JSON of the organized search queries
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES research_queries (query_id),
                FOREIGN KEY (session_id) REFERENCES sessions (session_id))''')
        #worker results
        cursor.execute(''' CREATE TABLE IF NOT EXISTS worker_results(
                       result_id TEXT PRIMARY KEY,
                structure_id TEXT,
                session_id TEXT,
                worker_type TEXT,  -- 'introduction', 'background', 'research_findings', 'application', 'summary'
                queries TEXT,  -- JSON array of queries processed
                raw_summaries TEXT,  -- JSON array of raw summaries
                compiled_result TEXT,  -- Final compiled result
                processing_time REAL,  -- Time taken to process
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (structure_id) REFERENCES research_structures (structure_id),
                FOREIGN KEY (session_id) REFERENCES sessions (session_id))''')
        
         # Final reports table - stores the complete research reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS final_reports (
                report_id TEXT PRIMARY KEY,
                session_id TEXT,
                structure_id TEXT,
                report_data TEXT,  -- JSON of the complete report
                word_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (structure_id) REFERENCES research_structures (structure_id)
            )
        ''')
        #user feedback table
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_feedback(feedback_id TEXT PRIMARY KEY,
                session_id TEXT,
                report_id TEXT,
                rating INTEGER,  -- 1-5 rating
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (report_id) REFERENCES final_reports (report_id))''')

        #create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id on sessions (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at on sessions (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_queries_session_id on research_queries (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_worker_results_sessions_id on worker_results (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_final_reports_session_id on final_reports (session_id)')
        
        conn.commit()
        conn.close()

    def create_session(self, user_id: str = None, metadata: Dict = None):
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO sessions (session_id, user_id, metadata)
            VALUES (?, ?, ?)
        ''', (session_id, user_id, json.dumps(metadata) if metadata else None))
        conn.commit()
        conn.close()
        return session_id

    def save_research_queries(self, session_id: str, original_query: str, generated_queries: List[str]) -> str:
        """Save the original query and the generated mutiple queries"""
        query_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO research_queries(query_id, session_id, original_query, generated_queries)
            VALUES (?, ?, ?, ?)
        ''', (query_id, session_id, original_query, json.dumps(generated_queries)))
        conn.commit()
        conn.close()
        return query_id

    def save_research_structure(self, query_id: str, session_id: str, structure_data: Dict) -> str:
        """save the organized research structure"""

        structure_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO research_structure(structure_id, query_id, session_id, structure_data)
            VALUES (?, ?, ?, ?)
        ''', (structure_id, query_id, session_id, json.dumps(structure_data)))

        conn.commit()
        conn.close()
        return structure_id

    def save_worker_result(self, structure_id: str, session_id: str, worker_type: str, 
                          queries: List[str], raw_summaries: List[str], 
                          compiled_result: str, processing_time: float) -> str:
        """Save individual worker results"""
        result_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO worker_results 
            (result_id, structure_id, session_id, worker_type, queries, raw_summaries, compiled_result, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (result_id, structure_id, session_id, worker_type, 
              json.dumps(queries), json.dumps(raw_summaries), compiled_result, processing_time))
        
        conn.commit()
        conn.close()
        return result_id

    def save_final_report(self, session_id: str, structure_id: str, report_data: Dict) -> str:
        """Save the final compiled report"""
        report_id = str(uuid.uuid4())
        
        # Calculate word count
        word_count = 0
        for section_content in report_data.values():
            if isinstance(section_content, str):
                word_count += len(section_content.split())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO final_reports (report_id, session_id, structure_id, report_data, word_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (report_id, session_id, structure_id, json.dumps(report_data), word_count))
        
        conn.commit()
        conn.close()
        return report_id


    def get_session_data(self, session_id:str) -> Dict:
        """retrieve all data for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        #get session info
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session = cursor.fetchone()

        #get research queries
        cursor.execute('SELECT * FROM research_queries WHERE session_id = ?', (session_id,))
        queries = cursor.fetchall()

        #get research structure
        cursor.execute('SELECT * FROM research_structure WHERE session_id = ?', (session_id,))
        structures = cursor.fetchall()

        #get worker results
        cursor.execute('SELECT * FROM worker_results WHERE session_id = ?', (session_id,))
        worker_results = cursor.fetchone()

        #get final report 
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        final_report = cursor.fetchall()

        conn.close()

        return {
            'session': session,
            'queries': queries,
            'structures': structures,
            'worker_results': worker_results,
            'reports': final_report

        }

    def update_session_access(self, session_id:str):
        """update the last accessed timestamp for the session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''UPDATE sessions
                       SET last_accessed = CURRENT_TIMESTAMP
                       WHERE session_id = ?
                       ''',(session_id,))


        conn.commit()
        conn.close()

    def get_user_session(self, user_id:str, limit: int = 10) -> List:
        """Get current session for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''SELECT session_id, created_at, last_accessed, status
            FROM sessions 
            WHERE user_id = ? 
            ORDER BY last_accessed DESC 
            LIMIT ?''',
            (user_id, limit))
        
        sessions = cursor.fetchall()
        conn.close()
        return sessions


    def save_user_feedback(self, session_id: str, report_id: str, rating: int, comments: str = None) -> str:
        """save user feedback on a report"""
        feedback_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO user_feedback (feedback_id, session_id, report_id, rating, comments)
            VALUES (?, ?, ?, ?, ?)
        ''', (feedback_id, session_id, report_id, rating, comments))
        conn.commit()
        conn.close()
        return feedback_id


    def cleanup_old_sessions(self, days: int = 40):
        """cleanup sessions older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM sessions 
            WHERE last_accessed < datetime('now', '-{} days')
        '''.format(days))

        conn.commit()
        conn.commit()

        